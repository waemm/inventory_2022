"""
spaCy Hybrid NER Predictor for Bioresource Extraction
======================================================

Integrates EntityRuler + Statistical NER with alias resolution.
Compatible with existing pipeline but provides enhanced capabilities.

Features:
- High-precision extraction of known bioresources (EntityRuler)
- Discovery of new/unknown bioresources (Statistical NER)
- Alias resolution (links short/long forms via canonical IDs)

Usage:
    from src.ner_predict_spacy import SpacyNERPredictor

    # Initialize predictor
    predictor = SpacyNERPredictor("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

    # Run prediction
    papers_df = pd.read_csv('papers.csv')  # Must have: pubmed_id, title, abstract
    results = predictor.predict(papers_df)

    # Or save to CSV
    predictor.predict_to_csv(papers_df, 'output.csv')
"""

import spacy
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SpacyNERPredictor:
    """
    Hybrid NER predictor using spaCy EntityRuler + Statistical NER.

    Features:
    - High-precision extraction of known bioresources (EntityRuler)
    - Discovery of new/unknown bioresources (Statistical NER)
    - Alias resolution (links short/long forms via canonical IDs)
    """

    def __init__(self, model_path: str = "spacy_hybrid_ner/models/ner_hybrid_v2_com_ful"):
        """
        Initialize predictor.

        Args:
            model_path: Path to trained spaCy hybrid pipeline

        Raises:
            FileNotFoundError: If model path doesn't exist
            ValueError: If pipeline components are invalid
        """
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        logger.info(f"Loading spaCy hybrid pipeline from {model_path}")
        self.nlp = spacy.load(str(model_path))

        # Verify pipeline components and order
        expected_order = ["entity_ruler", "ner"]
        actual_order = [name for name in self.nlp.pipe_names if name in expected_order]

        if actual_order != expected_order:
            raise ValueError(
                f"Pipeline order incorrect! Expected {expected_order}, "
                f"got {actual_order} from full pipeline: {self.nlp.pipe_names}"
            )

        logger.info(f"✓ Pipeline loaded successfully: {self.nlp.pipe_names}")

    def predict(
        self,
        papers_df: pd.DataFrame,
        text_column: Optional[str] = None,
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Extract bioresource entities from papers with alias resolution.

        Args:
            papers_df: DataFrame with columns ['pubmed_id', 'title', 'abstract']
                      or a pre-concatenated text column
            text_column: Optional name of column containing pre-concatenated text.
                        If None, will concatenate title + abstract.
            batch_size: Number of papers to process in each batch (default: 32)
                       Higher values = faster but more memory usage

        Returns:
            List of dicts with extracted entities and metadata:
                [{
                    'pmid': str,
                    'entity_count': int,
                    'entities': List[Dict],  # Individual entity mentions
                    'resources': List[Dict]  # Grouped by canonical ID
                }]

        Example:
            >>> predictor = SpacyNERPredictor()
            >>> papers = pd.read_csv('papers.csv')
            >>> results = predictor.predict(papers)
            >>> print(results[0]['resources'])
            [
                {
                    'canonical_id': 'PDB',
                    'mentions': ['PDB', 'Protein Data Bank'],
                    'source': 'known'
                },
                ...
            ]
        """
        if 'pubmed_id' not in papers_df.columns:
            raise ValueError("DataFrame must have 'pubmed_id' column")

        # Validate batch_size parameter
        if batch_size < 1:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if batch_size > 1000:
            logger.warning(
                f"Large batch_size ({batch_size}) may cause memory issues. "
                f"Consider using batch_size <= 100 for most workloads."
            )

        logger.info(f"Processing {len(papers_df)} papers with batch_size={batch_size}...")

        # Prepare texts and metadata upfront
        texts_data = []
        for idx, paper in papers_df.iterrows():
            # Get text
            if text_column and text_column in paper:
                text = str(paper[text_column])
            elif 'text' in paper and pd.notna(paper['text']):
                text = str(paper['text'])
            else:
                # Concatenate title + abstract
                title = str(paper.get('title', ''))
                abstract = str(paper.get('abstract', ''))
                text = f"{title} {abstract}".strip()

            texts_data.append({
                'pmid': paper['pubmed_id'],
                'text': text,
                'is_valid': len(text) >= 10
            })

        # Separate valid and invalid texts for efficiency
        valid_texts_data = [d for d in texts_data if d['is_valid']]
        invalid_texts_data = [d for d in texts_data if not d['is_valid']]

        # Log skipped papers
        if invalid_texts_data:
            logger.info(f"  Skipping {len(invalid_texts_data)} papers with insufficient text")

        # Initialize results
        results = []
        papers_with_entities = 0
        processed_count = 0

        # Add empty results for invalid texts (don't process through pipeline)
        for data in invalid_texts_data:
            results.append({
                'pmid': data['pmid'],
                'entity_count': 0,
                'entities': [],
                'resources': []
            })
            processed_count += 1

        # Batch process ONLY valid texts with spaCy's .pipe() for 2-5× speedup
        for data, doc in zip(valid_texts_data,
                            self.nlp.pipe([d['text'] for d in valid_texts_data],
                                         batch_size=batch_size)):
            pmid = data['pmid']

            # Extract entities with metadata
            entities = []
            for ent in doc.ents:
                entity_data = {
                    'text': ent.text,
                    'label': ent.label_,
                    'start_char': ent.start_char,
                    'end_char': ent.end_char,
                    'canonical_id': ent.ent_id_ if ent.ent_id_ else None,
                    'source': 'ruler' if ent.ent_id_ else 'statistical'
                }
                entities.append(entity_data)

            # Aggregate by canonical ID (alias resolution!)
            resources = self._group_by_canonical_id(entities)

            if len(entities) > 0:
                papers_with_entities += 1

            results.append({
                'pmid': pmid,
                'entity_count': len(entities),
                'entities': entities,
                'resources': resources
            })

            processed_count += 1

            # Progress logging
            if processed_count % 100 == 0:
                logger.info(f"  Processed {processed_count}/{len(papers_df)} papers...")

        logger.info(
            f"✓ Extracted entities from {papers_with_entities}/{len(papers_df)} papers "
            f"({papers_with_entities/len(papers_df)*100:.1f}%)"
        )

        return results

    def _group_by_canonical_id(self, entities: List[Dict]) -> List[Dict]:
        """
        Group entities by canonical ID (alias resolution).

        Args:
            entities: List of entity dicts

        Returns:
            List of resource dicts with all aliases grouped:
                [{
                    'canonical_id': str or None,
                    'mentions': List[str],
                    'source': 'known' or 'discovered'
                }]
        """
        resources = {}

        for ent in entities:
            canonical = ent['canonical_id']

            if canonical:
                # Known resource with canonical ID
                if canonical not in resources:
                    resources[canonical] = {
                        'canonical_id': canonical,
                        'mentions': [],
                        'source': 'known'
                    }
                resources[canonical]['mentions'].append(ent['text'])
            else:
                # Unknown resource (from statistical NER)
                # Create temporary ID
                temp_id = f"UNKNOWN_{ent['text']}"
                if temp_id not in resources:
                    resources[temp_id] = {
                        'canonical_id': None,
                        'mentions': [ent['text']],
                        'source': 'discovered'
                    }

        return list(resources.values())

    def predict_to_csv(
        self,
        papers_df: pd.DataFrame,
        output_path: str,
        text_column: Optional[str] = None,
        batch_size: int = 32
    ) -> pd.DataFrame:
        """
        Predict and save results to CSV.

        Args:
            papers_df: Input papers
            output_path: Path to save results CSV
            text_column: Optional name of text column
            batch_size: Number of papers to process in each batch (default: 32)

        Returns:
            DataFrame with flattened results (one row per entity)

        Output CSV columns:
            - pmid: PubMed ID
            - entity_text: Extracted entity text
            - entity_label: Entity label (e.g., BIO_RESOURCE)
            - canonical_id: Canonical resource ID (or None for discovered entities)
            - source: 'ruler' or 'statistical'
            - start_char: Character offset start
            - end_char: Character offset end
        """
        results = self.predict(papers_df, text_column=text_column, batch_size=batch_size)

        # Flatten for CSV
        rows = []
        for result in results:
            for ent in result['entities']:
                rows.append({
                    'pmid': result['pmid'],
                    'entity_text': ent['text'],
                    'entity_label': ent['label'],
                    'canonical_id': ent['canonical_id'],
                    'source': ent['source'],
                    'start_char': ent['start_char'],
                    'end_char': ent['end_char']
                })

        df_output = pd.DataFrame(rows)
        df_output.to_csv(output_path, index=False)
        logger.info(f"✓ Results saved to {output_path}")

        return df_output

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded pipeline.

        Returns:
            Dictionary with pipeline metadata
        """
        ruler = self.nlp.get_pipe("entity_ruler")

        return {
            'pipeline_components': self.nlp.pipe_names,
            'entityruler_patterns': len(ruler.patterns) if hasattr(ruler, 'patterns') else 0,
            'ner_labels': list(self.nlp.get_pipe("ner").labels) if "ner" in self.nlp.pipe_names else []
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Load test papers
    test_papers = pd.read_csv('spacy_hybrid_ner/data/ner_corpus_splits/test.csv').head(10)

    # Initialize predictor
    predictor = SpacyNERPredictor("spacy_hybrid_ner/models/ner_hybrid_v2_com_ful")

    # Print pipeline info
    print("\nPipeline Info:")
    print(predictor.get_pipeline_info())

    # Run prediction
    results = predictor.predict(test_papers)

    # Print sample results
    print("\nSample Results:")
    for result in results[:3]:
        print(f"\nPMID: {result['pmid']}")
        print(f"Entities found: {result['entity_count']}")
        for res in result['resources']:
            print(f"  {res['canonical_id']}: {set(res['mentions'])}")

    # Save to CSV
    predictor.predict_to_csv(test_papers, 'test_spacy_ner_output.csv')
    print("\n✓ Test complete!")
