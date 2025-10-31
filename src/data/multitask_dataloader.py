"""
Multi-Task DataLoader for Biomedical Classification and NER

This module provides data loading utilities for multi-task learning with metadata:
1. Loads augmented classification and NER datasets with metadata features
2. Oversamples NER data to balance class distribution
3. Creates mixed batches with task indicators
4. Handles proper tokenization and metadata extraction

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-10-31
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# Metadata feature column names (28 usable features - excluding text fields)
# Note: We exclude text fields like pubType, keywords, meshTerms, journalTitle, etc.
# as they require separate encoding (already captured in TF-IDF features)
BOOLEAN_FEATURES = [
    'hasDbCrossReferences', 'hasData', 'hasSuppl', 'isOpenAccess',
    'inPMC', 'inEPMC', 'hasPDF', 'hasBook',
    'is_research_article', 'is_review_article'
]

NUMERICAL_FEATURES = [
    'log_citations', 'years_since_pub', 'citedByCount', 'pubYear'
]

CATEGORICAL_FEATURES = [
    'meshTerms_missing', 'keywords_missing'
]

TFIDF_FEATURES = [
    'mesh_tfidf_0', 'mesh_tfidf_1', 'mesh_tfidf_2', 'mesh_tfidf_3',
    'mesh_tfidf_4', 'mesh_tfidf_5', 'mesh_tfidf_6',
    'keyword_tfidf_0', 'keyword_tfidf_1', 'keyword_tfidf_2',
    'keyword_tfidf_3', 'keyword_tfidf_4'
]

ALL_METADATA_FEATURES = (
    BOOLEAN_FEATURES + NUMERICAL_FEATURES + CATEGORICAL_FEATURES + TFIDF_FEATURES
)


class MultiTaskDataset(Dataset):
    """
    Combined dataset for classification + NER with metadata.

    This dataset:
    1. Loads both classification and NER samples with metadata
    2. Oversamples NER data to balance class distribution
    3. Returns mixed batches with task indicators
    4. Properly extracts and normalizes metadata features

    Args:
        classif_path: Path to augmented classification CSV
        ner_path: Path to augmented NER CSV
        tokenizer: HuggingFace tokenizer
        max_length_classif: Max sequence length for classification (256)
        max_length_ner: Max sequence length for NER (512)
        oversample_ner: Whether to oversample NER to match classification count
        test_mode: If True, use only first 50 samples per task
        metadata_features: List of metadata feature names to use

    Example:
        >>> tokenizer = AutoTokenizer.from_pretrained('roberta-base')
        >>> dataset = MultiTaskDataset(
        ...     classif_path='data/augmented/classif_train_with_metadata.csv',
        ...     ner_path='data/augmented/ner_train_with_metadata.csv',
        ...     tokenizer=tokenizer
        ... )
        >>> sample = dataset[0]
        >>> print(sample.keys())
    """

    def __init__(
        self,
        classif_path: str,
        ner_path: str,
        tokenizer: AutoTokenizer,
        max_length_classif: int = 256,
        max_length_ner: int = 512,
        oversample_ner: bool = True,
        test_mode: bool = False,
        metadata_features: Optional[List[str]] = None
    ):
        self.tokenizer = tokenizer
        self.max_length_classif = max_length_classif
        self.max_length_ner = max_length_ner

        # Use default metadata features if not specified
        if metadata_features is None:
            metadata_features = ALL_METADATA_FEATURES

        self.metadata_features = metadata_features
        self.n_metadata_features = len(metadata_features)

        logger.info(f"Loading classification data from: {classif_path}")
        self.classif_df = pd.read_csv(classif_path)

        logger.info(f"Loading NER data from: {ner_path}")
        self.ner_df = pd.read_csv(ner_path)

        # Test mode: use small subset
        if test_mode:
            logger.info("TEST_MODE: Using first 50 samples per task")
            self.classif_df = self.classif_df.head(50)
            self.ner_df = self.ner_df.head(50)

        # Validate metadata features exist
        self._validate_metadata_features()

        # Oversample NER to match classification count
        if oversample_ner and len(self.ner_df) < len(self.classif_df):
            n_repeats = int(np.ceil(len(self.classif_df) / len(self.ner_df)))
            logger.info(f"Oversampling NER: {len(self.ner_df)} → {len(self.ner_df) * n_repeats}")
            self.ner_df = pd.concat([self.ner_df] * n_repeats, ignore_index=True)
            self.ner_df = self.ner_df.iloc[:len(self.classif_df)]  # Trim to exact match

        # Create combined index with task labels
        self.samples = []

        # Add classification samples
        for idx in range(len(self.classif_df)):
            self.samples.append({
                'task': 'classification',
                'dataset_idx': idx,
                'dataset': 'classif'
            })

        # Add NER samples
        for idx in range(len(self.ner_df)):
            self.samples.append({
                'task': 'ner',
                'dataset_idx': idx,
                'dataset': 'ner'
            })

        logger.info(f"Dataset created:")
        logger.info(f"  - Classification samples: {len(self.classif_df)}")
        logger.info(f"  - NER samples: {len(self.ner_df)}")
        logger.info(f"  - Total samples: {len(self.samples)}")
        logger.info(f"  - Metadata features: {self.n_metadata_features}")

    def _validate_metadata_features(self):
        """Verify that all metadata features exist in both datasets."""
        classif_cols = set(self.classif_df.columns)
        ner_cols = set(self.ner_df.columns)

        for feature in self.metadata_features:
            if feature not in classif_cols:
                raise ValueError(f"Metadata feature '{feature}' not found in classification data")
            if feature not in ner_cols:
                raise ValueError(f"Metadata feature '{feature}' not found in NER data")

        logger.info(f"Validated {len(self.metadata_features)} metadata features")

    def _extract_metadata(self, row: pd.Series) -> np.ndarray:
        """
        Extract and normalize metadata features from a row.

        Args:
            row: DataFrame row containing metadata columns

        Returns:
            metadata: [n_metadata_features] numpy array
        """
        metadata = []
        for feature in self.metadata_features:
            value = row[feature]

            # Handle missing values
            if pd.isna(value):
                value = 0.0

            # Convert to float
            metadata.append(float(value))

        return np.array(metadata, dtype=np.float32)

    def _process_classification_sample(self, idx: int) -> Dict:
        """Process classification sample."""
        row = self.classif_df.iloc[idx]

        # Extract text
        title = str(row['title']) if pd.notna(row['title']) else ""
        abstract = str(row['abstract']) if pd.notna(row['abstract']) else ""
        text = f"{title} [SEP] {abstract}".strip()

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length_classif,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Extract label (curation_score: 0 or 1)
        label = int(row['curation_score'])

        # Extract metadata
        metadata = self._extract_metadata(row)

        return {
            'task': 'classification',
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': torch.tensor(label, dtype=torch.long),
            'metadata': torch.tensor(metadata, dtype=torch.float32)
        }

    def _process_ner_sample(self, idx: int) -> Dict:
        """
        Process NER sample with BIO tagging.

        For this MVP, we'll use a simple approach:
        - Tag the resource name in the abstract with B-RESOURCE, I-RESOURCE
        - All other tokens are O (outside)
        """
        row = self.ner_df.iloc[idx]

        # Extract text
        title = str(row['title']) if pd.notna(row['title']) else ""
        abstract = str(row['abstract']) if pd.notna(row['abstract']) else ""
        text = f"{title} [SEP] {abstract}".strip()

        # Extract resource name for tagging
        resource_name = str(row['full_name']) if pd.notna(row['full_name']) else ""

        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length_ner,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
            return_offsets_mapping=True
        )

        # Create BIO labels
        labels = self._create_bio_labels(
            text,
            resource_name,
            encoding['offset_mapping'].squeeze(0)
        )

        # Extract metadata
        metadata = self._extract_metadata(row)

        return {
            'task': 'ner',
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': labels,
            'metadata': torch.tensor(metadata, dtype=torch.float32)
        }

    def _create_bio_labels(
        self,
        text: str,
        resource_name: str,
        offset_mapping: torch.Tensor
    ) -> torch.Tensor:
        """
        Create BIO labels for token sequence.

        Label mapping: 0=O, 1=B-RESOURCE, 2=I-RESOURCE

        Args:
            text: Full text string
            resource_name: Resource name to tag
            offset_mapping: Token offset mapping [seq_len, 2]

        Returns:
            labels: [seq_len] tensor of BIO labels
        """
        seq_len = offset_mapping.shape[0]
        labels = torch.zeros(seq_len, dtype=torch.long)  # Default: all O

        if not resource_name or len(resource_name.strip()) == 0:
            return labels

        # Find resource name in text (case-insensitive)
        text_lower = text.lower()
        resource_lower = resource_name.lower().strip()

        # Find all occurrences
        start_idx = 0
        resource_spans = []

        while True:
            pos = text_lower.find(resource_lower, start_idx)
            if pos == -1:
                break
            resource_spans.append((pos, pos + len(resource_lower)))
            start_idx = pos + 1

        # Tag tokens that overlap with resource spans
        for token_idx in range(seq_len):
            token_start, token_end = offset_mapping[token_idx].tolist()

            # Skip special tokens (offset = 0,0)
            if token_start == 0 and token_end == 0:
                labels[token_idx] = -100  # Ignore in loss
                continue

            # Check if token overlaps with any resource span
            is_first_token = True
            for span_start, span_end in resource_spans:
                if token_start < span_end and token_end > span_start:
                    # Token overlaps with resource
                    if token_start == span_start or is_first_token:
                        labels[token_idx] = 1  # B-RESOURCE
                    else:
                        labels[token_idx] = 2  # I-RESOURCE
                    break

        return labels

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict:
        """Get sample by index."""
        sample_info = self.samples[idx]
        task = sample_info['task']
        dataset_idx = sample_info['dataset_idx']

        if task == 'classification':
            return self._process_classification_sample(dataset_idx)
        else:
            return self._process_ner_sample(dataset_idx)


def multitask_collate_fn(batch: List[Dict]) -> Dict:
    """
    Custom collate function to handle mixed sequence lengths.

    Classification samples have max_length=256, NER has max_length=512.
    We group by task and create homogeneous batches.

    Args:
        batch: List of samples from dataset

    Returns:
        collated_batch: Dictionary with batched tensors
    """
    # All samples in a batch should be the same task (enforced by sampler)
    # But we'll handle mixed batches gracefully
    tasks = [sample['task'] for sample in batch]

    # Check if homogeneous
    if len(set(tasks)) > 1:
        # Mixed batch - take only the first task type
        task = tasks[0]
        batch = [sample for sample in batch if sample['task'] == task]

    # Stack tensors
    return {
        'task': [sample['task'] for sample in batch],
        'input_ids': torch.stack([sample['input_ids'] for sample in batch]),
        'attention_mask': torch.stack([sample['attention_mask'] for sample in batch]),
        'labels': torch.stack([sample['labels'] for sample in batch]),
        'metadata': torch.stack([sample['metadata'] for sample in batch])
    }


def create_multitask_dataloaders(
    classif_train_path: str,
    ner_train_path: str,
    classif_val_path: Optional[str] = None,
    ner_val_path: Optional[str] = None,
    tokenizer_name: str = 'roberta-base',
    batch_size: int = 16,
    test_mode: bool = False,
    num_workers: int = 0,
    **kwargs
) -> Tuple[DataLoader, Optional[DataLoader]]:
    """
    Create multi-task dataloaders for training and validation.

    Args:
        classif_train_path: Path to classification training CSV
        ner_train_path: Path to NER training CSV
        classif_val_path: Path to classification validation CSV (optional)
        ner_val_path: Path to NER validation CSV (optional)
        tokenizer_name: HuggingFace tokenizer name
        batch_size: Batch size
        test_mode: Use small subset for testing
        num_workers: Number of dataloader workers
        **kwargs: Additional arguments for MultiTaskDataset

    Returns:
        train_loader: Training dataloader
        val_loader: Validation dataloader (None if validation paths not provided)

    Example:
        >>> train_loader, val_loader = create_multitask_dataloaders(
        ...     classif_train_path='data/augmented/classif_train_with_metadata.csv',
        ...     ner_train_path='data/augmented/ner_train_with_metadata.csv',
        ...     batch_size=16,
        ...     test_mode=True
        ... )
    """
    logger.info(f"Loading tokenizer: {tokenizer_name}")
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    # Create training dataset
    train_dataset = MultiTaskDataset(
        classif_path=classif_train_path,
        ner_path=ner_train_path,
        tokenizer=tokenizer,
        test_mode=test_mode,
        **kwargs
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        collate_fn=multitask_collate_fn
    )

    # Create validation dataset if paths provided
    val_loader = None
    if classif_val_path and ner_val_path:
        val_dataset = MultiTaskDataset(
            classif_path=classif_val_path,
            ner_path=ner_val_path,
            tokenizer=tokenizer,
            test_mode=test_mode,
            oversample_ner=False,  # Don't oversample validation
            **kwargs
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=True,
            collate_fn=multitask_collate_fn
        )

    logger.info(f"Created dataloaders:")
    logger.info(f"  - Training batches: {len(train_loader)}")
    if val_loader:
        logger.info(f"  - Validation batches: {len(val_loader)}")

    return train_loader, val_loader


if __name__ == "__main__":
    # Test dataloader
    logging.basicConfig(level=logging.INFO)

    train_loader, _ = create_multitask_dataloaders(
        classif_train_path='data/augmented/classif_train_with_metadata.csv',
        ner_train_path='data/augmented/ner_train_with_metadata.csv',
        batch_size=4,
        test_mode=True
    )

    # Test batch
    batch = next(iter(train_loader))
    print(f"\nSample batch:")
    for key, value in batch.items():
        if isinstance(value, torch.Tensor):
            print(f"  {key}: {value.shape}")
        else:
            print(f"  {key}: {value}")

    print("\nDataloader test passed!")
