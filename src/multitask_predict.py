"""
Multi-Task Model Inference Script for Phase 4

This script performs inference using the Phase 4 unified multi-task model
to predict both classification (bio-resource vs non-resource) and NER
(entity extraction) from scientific papers.

Usage:
    python src/multitask_predict.py \
        --input data/epmc_query_results_2022.csv \
        --metadata data/metadata/features_engineered.csv \
        --checkpoint checkpoint_best_ner.pt \
        --output-dir output/ \
        --batch-size 32 \
        --device cuda

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-11-03
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from tqdm import tqdm

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from models.multitask_model import BiomedicalMultiTaskModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# METADATA FEATURE CONFIGURATION
# ============================================================================

# The metadata features in EXACT order as used during training
# CRITICAL: This order MUST match the training configuration
# Total: 28 features (10 boolean + 4 numerical + 2 categorical + 12 TF-IDF)
METADATA_FEATURES = [
    # Boolean features (10 features)
    'hasDbCrossReferences',
    'hasData',
    'hasSuppl',
    'isOpenAccess',  # FIXED: Added missing feature
    'inPMC',
    'inEPMC',
    'hasPDF',
    'hasBook',
    'is_research_article',
    'is_review_article',

    # Numerical features (4 features)
    'log_citations',
    'years_since_pub',
    'citedByCount',  # FIXED: Added missing feature
    'pubYear',  # FIXED: Added missing feature

    # Categorical features (2 features)
    'meshTerms_missing',
    'keywords_missing',

    # TF-IDF features for MeSH terms (7 features)
    'mesh_tfidf_0',
    'mesh_tfidf_1',
    'mesh_tfidf_2',
    'mesh_tfidf_3',
    'mesh_tfidf_4',
    'mesh_tfidf_5',
    'mesh_tfidf_6',

    # TF-IDF features for keywords (5 features)
    'keyword_tfidf_0',
    'keyword_tfidf_1',
    'keyword_tfidf_2',
    'keyword_tfidf_3',
    'keyword_tfidf_4',
]

# Total: 28 features matching training configuration exactly

# Default imputation values for missing metadata
DEFAULT_METADATA_VALUES = {
    # Boolean features (10 features)
    'hasDbCrossReferences': 0,
    'hasData': 0,
    'hasSuppl': 0,
    'isOpenAccess': 0,  # FIXED: Added missing feature
    'inPMC': 0,
    'inEPMC': 0,
    'hasPDF': 0,
    'hasBook': 0,
    'is_research_article': 0,
    'is_review_article': 0,

    # Numerical features (4 features)
    'log_citations': 0.0,
    'years_since_pub': 0.0,
    'citedByCount': 0.0,  # FIXED: Added missing feature
    'pubYear': 0.0,  # FIXED: Added missing feature

    # Categorical features (2 features)
    'meshTerms_missing': 0,
    'keywords_missing': 0,

    # TF-IDF features (12 features)
    'mesh_tfidf_0': 0.0,
    'mesh_tfidf_1': 0.0,
    'mesh_tfidf_2': 0.0,
    'mesh_tfidf_3': 0.0,
    'mesh_tfidf_4': 0.0,
    'mesh_tfidf_5': 0.0,
    'mesh_tfidf_6': 0.0,
    'keyword_tfidf_0': 0.0,
    'keyword_tfidf_1': 0.0,
    'keyword_tfidf_2': 0.0,
    'keyword_tfidf_3': 0.0,
    'keyword_tfidf_4': 0.0,
}

# BIO tag mapping
ID2TAG = {
    0: 'O',
    1: 'B-COM',
    2: 'I-COM',
    3: 'B-FUL',
    4: 'I-FUL'
}

TAG2ID = {v: k for k, v in ID2TAG.items()}

# Classification label mapping
ID2LABEL = {
    0: 'not-bio-resource',
    1: 'bio-resource'
}


# ============================================================================
# DATASET CLASS
# ============================================================================

class InferenceDataset(Dataset):
    """Dataset for inference with tokenization and metadata."""

    def __init__(
        self,
        papers_df: pd.DataFrame,
        metadata_df: pd.DataFrame,
        tokenizer,
        max_length: int = 512,
        n_expected_features: int = 28
    ):
        """
        Args:
            papers_df: DataFrame with columns ['id', 'title', 'abstract']
            metadata_df: DataFrame with metadata features
            tokenizer: HuggingFace tokenizer
            max_length: Maximum sequence length
            n_expected_features: Number of features expected by model
        """
        self.papers_df = papers_df.copy()
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.n_expected_features = n_expected_features

        # CRITICAL FIX #2: Add publication_date handling
        if 'publication_date' not in self.papers_df.columns:
            logger.warning("'publication_date' column not found, using empty string")
            self.papers_df['publication_date'] = ''

        # CRITICAL FIX #5: Support both 'id' and 'ID' for flexibility
        id_col = 'ID' if 'ID' in self.papers_df.columns else 'id'
        self.papers_df['ID'] = self.papers_df[id_col].astype(str)

        id_col_meta = 'ID' if 'ID' in metadata_df.columns else 'id'
        metadata_df = metadata_df.copy()
        metadata_df['ID'] = metadata_df[id_col_meta].astype(str)

        # CRITICAL FIX #7: Filter out NaN IDs BEFORE merge to prevent cartesian product
        # Root cause: pandas merge treats all NaN values as matching, creating
        # a cartesian product explosion (e.g., 540 NaN papers × 496 NaN metadata = 267,840 rows!)
        papers_before = len(self.papers_df)
        metadata_before = len(metadata_df)

        # Filter: Keep only rows where ID is not 'nan' string (from astype(str))
        self.papers_df = self.papers_df[self.papers_df['ID'] != 'nan'].copy()
        metadata_df = metadata_df[metadata_df['ID'] != 'nan'].copy()

        papers_filtered = papers_before - len(self.papers_df)
        metadata_filtered = metadata_before - len(metadata_df)

        if papers_filtered > 0:
            logger.warning(
                f"Filtered {papers_filtered} papers with missing IDs "
                f"({papers_filtered / papers_before * 100:.1f}%) to prevent merge explosion"
            )
        if metadata_filtered > 0:
            logger.warning(
                f"Filtered {metadata_filtered} metadata rows with missing IDs "
                f"({metadata_filtered / metadata_before * 100:.1f}%)"
            )

        logger.info(
            f"Dataset sizes before merge: papers={len(self.papers_df)}, "
            f"metadata={len(metadata_df)}"
        )

        # Merge on uppercase ID (now safe from NaN cartesian product)
        merged_df = self.papers_df.merge(
            metadata_df,
            on='ID',
            how='left',
            suffixes=('', '_meta')
        )

        # Count papers with missing metadata
        missing_metadata = merged_df[METADATA_FEATURES[0]].isna().sum()
        if missing_metadata > 0:
            logger.warning(
                f"Found {missing_metadata} papers without metadata "
                f"({missing_metadata / len(merged_df) * 100:.1f}%). "
                f"Using default imputation."
            )

        # Impute missing metadata with defaults
        for feature in METADATA_FEATURES:
            if feature in merged_df.columns:
                merged_df[feature].fillna(DEFAULT_METADATA_VALUES[feature], inplace=True)
            else:
                logger.warning(f"Feature '{feature}' not found in metadata. Using default value.")
                merged_df[feature] = DEFAULT_METADATA_VALUES[feature]

        self.data = merged_df

        # Validate metadata features
        self._validate_metadata()

        logger.info(f"Initialized dataset with {len(self.data)} papers")

    def _validate_metadata(self):
        """Validate that all required metadata features are present."""
        missing_features = [f for f in METADATA_FEATURES if f not in self.data.columns]
        if missing_features:
            raise ValueError(
                f"Missing required metadata features: {missing_features}. "
                f"Available columns: {list(self.data.columns)}"
            )

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]

        # Extract text
        title = str(row['title']) if pd.notna(row['title']) else ''
        abstract = str(row['abstract']) if pd.notna(row['abstract']) else ''
        text = f"{title} {abstract}".strip()

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Extract metadata features in correct order
        metadata_values = [float(row[feature]) for feature in METADATA_FEATURES]

        # Pad with zeros if model expects more features than we have
        if len(metadata_values) < self.n_expected_features:
            padding = [0.0] * (self.n_expected_features - len(metadata_values))
            metadata_values.extend(padding)
            if idx == 0:  # Log once
                logger.warning(
                    f"Padding metadata from {len(METADATA_FEATURES)} to "
                    f"{self.n_expected_features} features with zeros"
                )

        metadata = torch.tensor(metadata_values, dtype=torch.float32)

        # CRITICAL FIX #2: Include publication_date in return
        publication_date = str(row.get('publication_date', '')) if pd.notna(row.get('publication_date', '')) else ''

        return {
            'id': row['ID'],  # CRITICAL FIX #5: Use uppercase ID
            'title': title,
            'abstract': abstract,
            'text': text,
            'publication_date': publication_date,
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'metadata': metadata
        }


# ============================================================================
# ENTITY EXTRACTION
# ============================================================================

def extract_entities_from_bio_tags(
    tokens: List[str],
    bio_tags: List[int],
    probabilities: List[float]
) -> List[Tuple[str, str, float]]:
    """
    DEPRECATED: Token-level extraction produces BPE artifacts.
    Use extract_entities_word_level() instead for clean entity extraction.

    Extract entities from BIO-tagged tokens.

    Args:
        tokens: List of tokens (words)
        bio_tags: List of BIO tag IDs [0=O, 1=B-COM, 2=I-COM, 3=B-FUL, 4=I-FUL]
        probabilities: Token-level probabilities for assigned tags

    Returns:
        List of (entity_text, entity_type, confidence) tuples
    """
    # CRITICAL FIX #4: Add validation
    if not (len(tokens) == len(bio_tags) == len(probabilities)):
        logger.error(
            f"Length mismatch: tokens={len(tokens)}, "
            f"bio_tags={len(bio_tags)}, probabilities={len(probabilities)}"
        )
        # Return empty list on validation failure
        return []

    entities = []
    current_entity = None

    for token, tag_id, prob in zip(tokens, bio_tags, probabilities):
        # CRITICAL FIX #4: Skip RoBERTa-specific special tokens
        # RoBERTa uses <s>, </s>, <pad>, <unk> (not [CLS], [SEP])
        if token in ['<s>', '</s>', '<pad>', '<unk>']:
            continue

        tag = ID2TAG[tag_id]

        if tag.startswith('B-'):  # Beginning of entity
            # Save previous entity if exists
            if current_entity:
                entities.append(current_entity)

            # Start new entity
            entity_type = tag[2:]  # 'COM' or 'FUL'
            current_entity = {
                'text': token,
                'type': entity_type,
                'probs': [prob]
            }

        elif tag.startswith('I-') and current_entity:  # Inside entity
            # Continue current entity
            entity_type = tag[2:]

            # Only continue if type matches
            if entity_type == current_entity['type']:
                # Add space before token (except for subwords)
                current_entity['text'] += f" {token}"
                current_entity['probs'].append(prob)
            else:
                # Type mismatch - save current and start new
                entities.append(current_entity)
                current_entity = {
                    'text': token,
                    'type': entity_type,
                    'probs': [prob]
                }

        else:  # Outside entity (O tag) or type mismatch
            if current_entity:
                entities.append(current_entity)
                current_entity = None

    # Don't forget last entity
    if current_entity:
        entities.append(current_entity)

    # Calculate average confidence per entity
    results = []
    for ent in entities:
        avg_prob = sum(ent['probs']) / len(ent['probs'])
        results.append((ent['text'], ent['type'], avg_prob))

    return results


def extract_entities_word_level(
    text: str,
    tokenizer,
    input_ids: torch.Tensor,
    bio_tags: List[int],
    probabilities: List[float],
    id2tag: Dict[int, str]
) -> List[Tuple[str, str, float]]:
    """
    Extract entities using word-level reconstruction (V2 approach).

    This function eliminates BPE tokenization artifacts by extracting clean text
    directly from the original string using word-level character spans.

    Args:
        text: Original text string (title + abstract)
        tokenizer: HuggingFace tokenizer with word_ids() support
        input_ids: Token IDs tensor [seq_len]
        bio_tags: BIO tag IDs for each token [seq_len]
        probabilities: Token-level probabilities [seq_len]
        id2tag: Mapping from tag IDs to tag strings {0: 'O', 1: 'B-COM', ...}

    Returns:
        List of (entity_text, entity_type, avg_confidence) tuples
        - entity_text: Clean text from original string (no BPE artifacts)
        - entity_type: 'COM' or 'FUL'
        - avg_confidence: Average token probability for the entity
    """
    # CRITICAL FIX #1: Add empty input validation
    if not text or not text.strip():
        logger.debug("Empty text input, returning no entities")
        return []

    # IMPROVEMENT #2: Add try-catch for tokenization
    try:
        # Step 1: Get word-level mappings from tokenizer
        encoding = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        word_ids = encoding.word_ids()[1:-1]  # Skip [CLS] and [SEP]
    except Exception as e:
        logger.error(f"Tokenization failed: {e}")
        return []

    # CRITICAL FIX #2: Add length validation
    expected_len = len(word_ids)
    actual_bio_len = len(bio_tags) - 2  # Minus [CLS] and [SEP]
    if expected_len != actual_bio_len:
        logger.error(
            f"Length mismatch: word_ids={expected_len}, bio_tags={actual_bio_len}. "
            f"Text: {text[:50]}..."
        )
        return []

    # Step 2: Build word_locs dict (word_id -> CharSpan)
    word_locs = {}
    for word_id in set(word_ids):
        if word_id is not None:
            word_locs[word_id] = encoding.word_to_chars(word_id)

    # IMPROVEMENT #3: Add word_locs validation
    if not word_locs:
        logger.debug(f"No valid words found in text: {text[:50]}...")
        return []

    # IMPROVEMENT #1: Add debug logging
    logger.debug(f"Processing {len(word_locs)} words for entity extraction")

    # Step 3: Process word-by-word (not token-by-token!)
    entities = []
    current_entity = None

    for word_id in sorted(word_locs.keys()):
        # Find all tokens for this word
        token_indices = [i for i, wid in enumerate(word_ids) if wid == word_id]

        # Get tags and probs for this word's tokens
        word_tags = [id2tag[bio_tags[i+1]] for i in token_indices]  # +1 for [CLS]
        word_probs = [probabilities[i+1] for i in token_indices]

        # Determine word's BIO tag (prioritize B-tags, then I-tags)
        if any(tag.startswith('B-') for tag in word_tags):
            word_tag = next(tag for tag in word_tags if tag.startswith('B-'))
        elif any(tag.startswith('I-') for tag in word_tags):
            word_tag = next(tag for tag in word_tags if tag.startswith('I-'))
        else:
            word_tag = 'O'

        # Extract clean word text from original string
        span = word_locs[word_id]
        word_text = text[span.start:span.end]

        # Entity assembly logic (same as V2)
        if word_tag.startswith('B-'):
            if current_entity:
                entities.append(current_entity)

            entity_type = word_tag[2:]  # 'COM' or 'FUL'
            current_entity = {
                'text': word_text,
                'type': entity_type,
                'probs': word_probs
            }

        elif word_tag.startswith('I-') and current_entity:
            entity_type = word_tag[2:]
            if entity_type == current_entity['type']:
                current_entity['text'] += ' ' + word_text
                current_entity['probs'].extend(word_probs)
            else:
                # Type mismatch - start new entity
                entities.append(current_entity)
                current_entity = {
                    'text': word_text,
                    'type': entity_type,
                    'probs': word_probs
                }

        else:  # O tag
            if current_entity:
                entities.append(current_entity)
                current_entity = None

    # Don't forget last entity
    if current_entity:
        entities.append(current_entity)

    # IMPROVEMENT #1: Add debug logging
    logger.debug(f"Extracted {len(entities)} entities before quality filtering")

    # Calculate average confidence and apply V2 quality filters
    results = []
    for ent in entities:
        entity_text = ent['text'].strip()

        # CRITICAL FIX #3: Add probability list validation
        if not ent['probs']:
            logger.warning(f"Entity '{entity_text}' has no probabilities, skipping")
            continue

        avg_prob = sum(ent['probs']) / len(ent['probs'])

        # V2 quality filters: length > 1, no URLs, length <= 100
        if (len(entity_text) > 1 and
            'http' not in entity_text.lower() and
            len(entity_text) <= 100):
            results.append((entity_text, ent['type'], avg_prob))
        else:
            # IMPROVEMENT #1: Add debug logging for filtered entities
            logger.debug(f"Filtered out entity: '{entity_text}' (length={len(entity_text)})")

    # IMPROVEMENT #1: Add debug logging
    logger.debug(f"Returned {len(results)} entities after quality filtering")

    return results


def tokens_to_words(tokenizer, input_ids: torch.Tensor) -> List[str]:
    """
    Convert token IDs back to words.

    DEPRECATED: Only used by deprecated extract_entities_from_bio_tags().
    New code should use extract_entities_word_level() instead.

    Args:
        tokenizer: HuggingFace tokenizer
        input_ids: Tensor of token IDs [seq_len]

    Returns:
        List of tokens (strings)
    """
    tokens = tokenizer.convert_ids_to_tokens(input_ids.cpu().numpy())
    return tokens


def deduplicate_phase4_output(ner_results: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate Phase 4 NER output using V2's proven deduplication logic.

    Converts Phase 4 wide format to V2 long format, applies V2 deduplication
    (which handles exact duplicates and case-insensitive matching), then
    converts back to Phase 4 format.

    Args:
        ner_results: DataFrame with columns [ID, text, publication_date,
                     common_name, common_prob, full_name, full_prob]

    Returns:
        Deduplicated DataFrame in same format as input
    """
    # Import V2 deduplication function
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from ner_predict import deduplicate

    # Convert Phase 4 wide format to V2 long format
    long_format = []
    for _, row in ner_results.iterrows():
        # Parse common_name entities (COM type)
        if pd.notna(row['common_name']) and row['common_name']:
            names = [n.strip() for n in str(row['common_name']).split(',') if n.strip()]
            probs = [p.strip() for p in str(row['common_prob']).split(',') if p.strip()]

            for name, prob in zip(names, probs):
                long_format.append({
                    'ID': row['ID'],
                    'text': row['text'],
                    'publication_date': row.get('publication_date', ''),
                    'mention': name,
                    'label': 'COM',
                    'prob': float(prob)
                })

        # Parse full_name entities (FUL type)
        if pd.notna(row['full_name']) and row['full_name']:
            names = [n.strip() for n in str(row['full_name']).split(',') if n.strip()]
            probs = [p.strip() for p in str(row['full_prob']).split(',') if p.strip()]

            for name, prob in zip(names, probs):
                long_format.append({
                    'ID': row['ID'],
                    'text': row['text'],
                    'publication_date': row.get('publication_date', ''),
                    'mention': name,
                    'label': 'FUL',
                    'prob': float(prob)
                })

    # Handle empty case
    if not long_format:
        logger.warning("No entities found for deduplication")
        return ner_results

    # Convert to DataFrame and apply V2 deduplication
    long_df = pd.DataFrame(long_format)
    logger.info(f"Before deduplication: {len(long_df)} entity instances")
    deduped_df = deduplicate(long_df)
    logger.info(f"After deduplication: {len(deduped_df)} entity instances")
    reduction = len(long_df) - len(deduped_df)
    if reduction > 0:
        logger.info(f"Removed {reduction} duplicates ({reduction/len(long_df)*100:.1f}%)")

    # Convert back to Phase 4 wide format
    results = []
    for paper_id in deduped_df['ID'].unique():
        paper_entities = deduped_df[deduped_df['ID'] == paper_id]

        # Get original row data
        orig_row = ner_results[ner_results['ID'] == paper_id].iloc[0]

        # Separate by entity type
        com_entities = paper_entities[paper_entities['label'] == 'COM']
        ful_entities = paper_entities[paper_entities['label'] == 'FUL']

        # Build entity strings
        common_names = ', '.join(com_entities['mention'].tolist())
        common_probs = ', '.join([f"{p:.3f}" for p in com_entities['prob'].tolist()])
        full_names = ', '.join(ful_entities['mention'].tolist())
        full_probs = ', '.join([f"{p:.3f}" for p in ful_entities['prob'].tolist()])

        results.append({
            'ID': paper_id,
            'text': orig_row['text'],
            'publication_date': orig_row.get('publication_date', ''),
            'common_name': common_names,
            'common_prob': common_probs,
            'full_name': full_names,
            'full_prob': full_probs
        })

    return pd.DataFrame(results)


# ============================================================================
# INFERENCE FUNCTIONS
# ============================================================================

def load_model(checkpoint_path: str, device: torch.device) -> BiomedicalMultiTaskModel:
    """
    Load the Phase 4 multi-task model from checkpoint.

    Args:
        checkpoint_path: Path to checkpoint file
        device: Device to load model on

    Returns:
        Loaded model in eval mode
    """
    logger.info(f"Loading model from checkpoint: {checkpoint_path}")

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Extract model configuration if available
    if 'config' in checkpoint:
        config = checkpoint['config']
        logger.info(f"Found config in checkpoint: {config}")
    else:
        # Use default configuration
        logger.warning("No config found in checkpoint, using defaults")
        # Try to infer from state dict
        state_dict = checkpoint.get('model_state_dict', checkpoint)

        # Check metadata projection layer size to infer n_metadata_features
        if 'metadata_projection.projection.weight' in state_dict:
            n_metadata = state_dict['metadata_projection.projection.weight'].shape[1]
            logger.info(f"Inferred n_metadata_features from checkpoint: {n_metadata}")
        else:
            n_metadata = 28  # Default

        config = {
            'n_metadata_features': n_metadata,
            'num_classes': 2,
            'num_ner_labels': 5,  # O, B-COM, I-COM, B-FUL, I-FUL
            'n_boolean_features': 10,
            'n_numerical_features': 2,
            'classification_dropout': 0.3,
            'ner_dropout': 0.1
        }

    # Determine base model from checkpoint or use default
    base_model = config.get(
        'model_name_or_path',
        'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'
    )

    # Create model
    model = BiomedicalMultiTaskModel(
        model_name_or_path=base_model,
        n_metadata_features=config.get('n_metadata_features', 28),
        num_classes=config.get('num_classes', 2),
        num_ner_labels=config.get('num_ner_labels', 5),
        n_boolean_features=config.get('n_boolean_features', 10),
        n_numerical_features=config.get('n_numerical_features', 2),
        classification_dropout=config.get('classification_dropout', 0.3),
        ner_dropout=config.get('ner_dropout', 0.1)
    )

    # Load state dict
    if 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
    else:
        state_dict = checkpoint

    # Load weights
    try:
        model.load_state_dict(state_dict, strict=True)
        logger.info("Successfully loaded model weights (strict mode)")
    except Exception as e:
        logger.warning(f"Failed strict loading, trying non-strict: {e}")
        model.load_state_dict(state_dict, strict=False)
        logger.info("Loaded model weights (non-strict mode)")

    # Move to device and set eval mode
    model.to(device)
    model.eval()

    logger.info(f"Model loaded successfully on {device}")
    logger.info(f"  - Metadata features: {model.n_metadata_features}")
    logger.info(f"  - Classification classes: {model.num_classes}")
    logger.info(f"  - NER labels: {model.num_ner_labels}")

    return model


def run_classification_inference(
    model: BiomedicalMultiTaskModel,
    dataloader: DataLoader,
    device: torch.device
) -> pd.DataFrame:
    """
    Run classification inference.

    Args:
        model: Trained multi-task model
        dataloader: DataLoader with papers
        device: Device to run on

    Returns:
        DataFrame with classification results
    """
    logger.info("Running classification inference...")

    results = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Classification"):
            # Move to device
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            metadata = batch['metadata'].to(device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                metadata=metadata,
                task='classification',
                return_auxiliary=False
            )

            # Get predictions
            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(logits, dim=-1)

            # CRITICAL FIX #3: Use uppercase 'ID' and include all required fields
            for i in range(len(batch['id'])):
                results.append({
                    'ID': str(batch['id'][i]),  # Uppercase!
                    'text': batch['text'][i],
                    'publication_date': batch.get('publication_date', [''] * len(batch['id']))[i],
                    'predicted_label': ID2LABEL[preds[i].item()],
                    'probability': probs[i][1].item(),  # Probability of bio-resource
                    'title': batch['title'][i],
                    'abstract': batch['abstract'][i]
                })

    results_df = pd.DataFrame(results)
    logger.info(f"Classification complete: {len(results_df)} papers processed")

    # Print summary statistics
    positive_count = (results_df['predicted_label'] == 'bio-resource').sum()
    logger.info(f"  - Bio-resources: {positive_count} ({positive_count/len(results_df)*100:.1f}%)")
    logger.info(f"  - Non-resources: {len(results_df) - positive_count} ({(len(results_df)-positive_count)/len(results_df)*100:.1f}%)")
    logger.info(f"  - Mean probability: {results_df['probability'].mean():.3f}")

    return results_df


def run_ner_inference(
    model: BiomedicalMultiTaskModel,
    dataloader: DataLoader,
    tokenizer,
    device: torch.device
) -> pd.DataFrame:
    """
    Run NER inference.

    Args:
        model: Trained multi-task model
        dataloader: DataLoader with papers
        tokenizer: Tokenizer for decoding
        device: Device to run on

    Returns:
        DataFrame with NER results in format compatible with downstream pipeline
    """
    logger.info("Running NER inference...")

    results = []
    total_entities = 0

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="NER"):
            # Move to device
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            metadata = batch['metadata'].to(device)

            # Forward pass
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                metadata=metadata,
                task='ner',
                return_auxiliary=False
            )

            # Get predictions [batch_size, seq_len, num_labels]
            logits = outputs['logits']
            probs = torch.softmax(logits, dim=-1)
            preds = torch.argmax(logits, dim=-1)

            # PHASE 4 POST-PROCESSING FIX: Use word-level extraction
            for i in range(len(batch['id'])):
                # Get predictions and probabilities for this sequence
                seq_preds = preds[i].cpu().numpy()
                seq_probs = probs[i].cpu().numpy()

                # Get probability of predicted tag for each token
                token_probs = [seq_probs[j, seq_preds[j]] for j in range(len(seq_preds))]

                # NEW: Word-level extraction with proper detokenization
                entities = extract_entities_word_level(
                    text=batch['text'][i],
                    tokenizer=tokenizer,
                    input_ids=input_ids[i],
                    bio_tags=seq_preds.tolist(),
                    probabilities=token_probs,
                    id2tag=ID2TAG
                )

                total_entities += len(entities)

                # Separate entities by type (COM vs FUL)
                com_entities = [(text, prob) for text, etype, prob in entities if etype == 'COM']
                ful_entities = [(text, prob) for text, etype, prob in entities if etype == 'FUL']

                # Format as comma-separated strings (matching ner_predict.py output)
                results.append({
                    'ID': str(batch['id'][i]),  # Uppercase!
                    'text': batch['text'][i],  # Combined title+abstract
                    'publication_date': batch.get('publication_date', [''] * len(batch['id']))[i],
                    'common_name': ', '.join([text for text, _ in com_entities]),
                    'common_prob': ', '.join([f"{prob:.3f}" for _, prob in com_entities]),
                    'full_name': ', '.join([text for text, _ in ful_entities]),
                    'full_prob': ', '.join([f"{prob:.3f}" for _, prob in ful_entities])
                })

    # Handle empty results with error handling
    if not results:
        logger.error("No results generated from NER inference!")
        return pd.DataFrame(columns=['ID', 'text', 'publication_date',
                                      'common_name', 'common_prob',
                                      'full_name', 'full_prob'])

    results_df = pd.DataFrame(results)
    logger.info(f"NER complete: {len(results_df)} papers processed")
    logger.info(f"  - Total entities extracted: {total_entities}")

    # Count papers with at least one entity
    papers_with_entities = (
        (results_df['common_name'] != '') | (results_df['full_name'] != '')
    ).sum()
    logger.info(f"  - Papers with entities: {papers_with_entities}")

    if len(results_df) > 0:
        logger.info(f"  - Avg entities per paper: {total_entities / len(results_df):.2f}")

    # Count entity types
    com_count = (results_df['common_name'] != '').sum()
    ful_count = (results_df['full_name'] != '').sum()
    logger.info(f"  - Papers with COM entities: {com_count}")
    logger.info(f"  - Papers with FUL entities: {ful_count}")

    return results_df


# ============================================================================
# COLLATE FUNCTION
# ============================================================================

def collate_fn(batch):
    """
    Custom collate function for DataLoader to handle mixed string/tensor data.

    CRITICAL FIX #6: Required for batching with string fields like 'id', 'title',
    'abstract', 'text', and 'publication_date'.

    Args:
        batch: List of samples from InferenceDataset.__getitem__

    Returns:
        Dictionary with batched data
    """
    return {
        'id': [item['id'] for item in batch],
        'title': [item['title'] for item in batch],
        'abstract': [item['abstract'] for item in batch],
        'text': [item['text'] for item in batch],
        'publication_date': [item['publication_date'] for item in batch],
        'input_ids': torch.stack([item['input_ids'] for item in batch]),
        'attention_mask': torch.stack([item['attention_mask'] for item in batch]),
        'metadata': torch.stack([item['metadata'] for item in batch])
    }


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Run inference with Phase 4 multi-task model',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Input/output arguments
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input CSV with papers (id, title, abstract)'
    )
    parser.add_argument(
        '--metadata',
        type=str,
        required=True,
        help='CSV with engineered features (28 metadata columns)'
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to Phase 4 model checkpoint'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        required=True,
        help='Output directory for results'
    )

    # Model arguments
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for inference'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='auto',
        choices=['auto', 'cuda', 'cpu', 'mps'],
        help='Device to run on (auto will detect GPU)'
    )
    parser.add_argument(
        '--max-length-classif',
        type=int,
        default=256,
        help='Max sequence length for classification'
    )
    parser.add_argument(
        '--max-length-ner',
        type=int,
        default=512,
        help='Max sequence length for NER'
    )
    parser.add_argument(
        '--num-workers',
        type=int,
        default=0,
        help='Number of dataloader workers'
    )

    args = parser.parse_args()

    # Validate inputs
    input_path = Path(args.input)
    metadata_path = Path(args.metadata)
    checkpoint_path = Path(args.checkpoint)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Determine device
    if args.device == 'auto':
        if torch.cuda.is_available():
            device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            device = torch.device('mps')
        else:
            device = torch.device('cpu')
    else:
        device = torch.device(args.device)

    logger.info(f"Using device: {device}")

    # Load tokenizer
    logger.info("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(
        'allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500'
    )

    # Load data
    logger.info(f"Loading input papers from: {input_path}")
    papers_df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(papers_df)} papers")

    logger.info(f"Loading metadata from: {metadata_path}")
    metadata_df = pd.read_csv(metadata_path)
    logger.info(f"Loaded metadata for {len(metadata_df)} papers")

    # Check required columns in papers
    required_cols = ['id', 'title', 'abstract']
    missing_cols = [col for col in required_cols if col not in papers_df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")

    # Load model
    model = load_model(str(checkpoint_path), device)

    # Get number of metadata features expected by model
    n_expected_features = model.n_metadata_features
    logger.info(f"Model expects {n_expected_features} metadata features")
    logger.info(f"CSV provides {len(METADATA_FEATURES)} metadata features")

    # ========================================================================
    # CLASSIFICATION INFERENCE
    # ========================================================================

    logger.info("\n" + "="*80)
    logger.info("CLASSIFICATION INFERENCE")
    logger.info("="*80)

    # Create dataset for classification
    classif_dataset = InferenceDataset(
        papers_df=papers_df,
        metadata_df=metadata_df,
        tokenizer=tokenizer,
        max_length=args.max_length_classif,
        n_expected_features=n_expected_features
    )

    # CRITICAL FIX #6: Add collate_fn for proper batching
    classif_dataloader = DataLoader(
        classif_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,  # Required for mixed string/tensor data
        num_workers=args.num_workers,
        pin_memory=True if device.type == 'cuda' else False
    )

    # Run classification
    start_time = time.time()
    classification_results = run_classification_inference(model, classif_dataloader, device)
    classif_time = time.time() - start_time

    # Save classification results
    classif_output = output_dir / 'classification_results.csv'
    classification_results.to_csv(classif_output, index=False)
    logger.info(f"Classification results saved to: {classif_output}")

    # ========================================================================
    # NER INFERENCE
    # ========================================================================

    logger.info("\n" + "="*80)
    logger.info("NER INFERENCE")
    logger.info("="*80)

    # Create dataset for NER
    ner_dataset = InferenceDataset(
        papers_df=papers_df,
        metadata_df=metadata_df,
        tokenizer=tokenizer,
        max_length=args.max_length_ner,
        n_expected_features=n_expected_features
    )

    # CRITICAL FIX #6: Add collate_fn for proper batching
    ner_dataloader = DataLoader(
        ner_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,  # Required for mixed string/tensor data
        num_workers=args.num_workers,
        pin_memory=True if device.type == 'cuda' else False
    )

    # Run NER
    start_time = time.time()
    ner_results = run_ner_inference(model, ner_dataloader, tokenizer, device)
    ner_time = time.time() - start_time

    # PHASE 4 POST-PROCESSING FIX: Apply deduplication
    logger.info("\nApplying deduplication to remove duplicate entities...")
    ner_results_deduped = deduplicate_phase4_output(ner_results)

    # Save NER results (deduplicated)
    ner_output = output_dir / 'ner_results.csv'
    ner_results_deduped.to_csv(ner_output, index=False)
    logger.info(f"NER results saved to: {ner_output}")

    # ========================================================================
    # SUMMARY
    # ========================================================================

    logger.info("\n" + "="*80)
    logger.info("INFERENCE SUMMARY")
    logger.info("="*80)
    logger.info(f"Total papers processed: {len(papers_df)}")
    logger.info(f"Classification time: {classif_time:.2f}s ({len(papers_df)/classif_time:.1f} papers/s)")
    logger.info(f"NER time: {ner_time:.2f}s ({len(papers_df)/ner_time:.1f} papers/s)")
    logger.info(f"Total time: {classif_time + ner_time:.2f}s")
    logger.info(f"\nOutput files:")
    logger.info(f"  - {classif_output}")
    logger.info(f"  - {ner_output}")
    logger.info("="*80)


if __name__ == '__main__':
    main()
