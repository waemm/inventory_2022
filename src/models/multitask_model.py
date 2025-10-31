"""
Multi-Task Learning Model for Biomedical Resource Classification and NER

This module implements a multi-task learning architecture that jointly trains:
1. Binary classification (bio-resource vs non-resource)
2. Named Entity Recognition (BIO tagging for resource names)
3. Auxiliary metadata prediction (for regularization)

Architecture:
- Shared RoBERTa encoder (with optional TAPT initialization)
- Metadata projection layer (34 features → 768 dims)
- Post-encoder fusion (concatenate text CLS + metadata projection)
- Task-specific heads with appropriate dropout rates
- Auxiliary prediction heads for boolean/numerical metadata

Author: Phase 4 Multi-Task Learning Implementation
Date: 2025-10-31
"""

import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MetadataProjection(nn.Module):
    """
    Projects metadata features to match RoBERTa hidden dimension.

    Architecture:
    - Linear projection: n_features → hidden_size
    - Layer normalization for stability
    - Dropout for regularization

    Args:
        n_features: Number of input metadata features (34)
        hidden_size: Target dimension (768 for RoBERTa-base)
        dropout: Dropout rate (default 0.1)
    """

    def __init__(self, n_features: int, hidden_size: int, dropout: float = 0.1):
        super().__init__()
        self.projection = nn.Linear(n_features, hidden_size)
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)

        # Initialize with small weights to prevent dominating text embeddings
        nn.init.xavier_uniform_(self.projection.weight, gain=0.1)
        nn.init.zeros_(self.projection.bias)

    def forward(self, metadata: torch.Tensor) -> torch.Tensor:
        """
        Args:
            metadata: [batch_size, n_features]

        Returns:
            projected: [batch_size, hidden_size]
        """
        projected = self.projection(metadata)
        projected = self.layer_norm(projected)
        projected = self.dropout(projected)
        return projected


class FusionLayer(nn.Module):
    """
    Fuses text embeddings with projected metadata.

    Architecture:
    - Concatenate CLS embedding + metadata projection
    - Linear transformation: (hidden_size * 2) → hidden_size
    - GELU activation
    - Dropout

    Args:
        hidden_size: RoBERTa hidden dimension (768)
        dropout: Dropout rate (default 0.1)
    """

    def __init__(self, hidden_size: int, dropout: float = 0.1):
        super().__init__()
        self.fusion = nn.Linear(hidden_size * 2, hidden_size)
        self.activation = nn.GELU()
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, text_embedding: torch.Tensor, metadata_embedding: torch.Tensor) -> torch.Tensor:
        """
        Args:
            text_embedding: [batch_size, hidden_size] - CLS token embedding
            metadata_embedding: [batch_size, hidden_size] - Projected metadata

        Returns:
            fused: [batch_size, hidden_size]
        """
        concatenated = torch.cat([text_embedding, metadata_embedding], dim=-1)
        fused = self.fusion(concatenated)
        fused = self.activation(fused)
        fused = self.layer_norm(fused)
        fused = self.dropout(fused)
        return fused


class ClassificationHead(nn.Module):
    """
    Binary classification head for bio-resource detection.

    Args:
        hidden_size: Input dimension (768)
        num_classes: Number of output classes (2: resource/non-resource)
        dropout: Dropout rate (0.3 recommended for classification)
    """

    def __init__(self, hidden_size: int, num_classes: int = 2, dropout: float = 0.3):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, fused_embedding: torch.Tensor) -> torch.Tensor:
        """
        Args:
            fused_embedding: [batch_size, hidden_size]

        Returns:
            logits: [batch_size, num_classes]
        """
        x = self.dropout(fused_embedding)
        logits = self.classifier(x)
        return logits


class NERHead(nn.Module):
    """
    Token-level classification head for Named Entity Recognition (BIO tagging).

    Architecture:
    - Broadcast metadata to all tokens
    - Linear layer: hidden_size → num_labels
    - Lower dropout (0.1) to preserve token-level information

    Args:
        hidden_size: Input dimension (768)
        num_labels: Number of BIO tags (3: B-RESOURCE, I-RESOURCE, O)
        dropout: Dropout rate (0.1 recommended for NER)
    """

    def __init__(self, hidden_size: int, num_labels: int = 3, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, sequence_output: torch.Tensor, metadata_embedding: torch.Tensor) -> torch.Tensor:
        """
        Args:
            sequence_output: [batch_size, seq_len, hidden_size] - All token embeddings
            metadata_embedding: [batch_size, hidden_size] - Projected metadata

        Returns:
            logits: [batch_size, seq_len, num_labels]
        """
        # Broadcast metadata to all tokens
        batch_size, seq_len, hidden_size = sequence_output.shape
        metadata_expanded = metadata_embedding.unsqueeze(1).expand(batch_size, seq_len, -1)

        # Add metadata information to each token (residual connection)
        enhanced_sequence = sequence_output + metadata_expanded

        x = self.dropout(enhanced_sequence)
        logits = self.classifier(x)
        return logits


class AuxiliaryMetadataHeads(nn.Module):
    """
    Auxiliary prediction heads for metadata features (regularization).

    Predicts metadata from text embeddings to encourage learning
    relevant representations and prevent overfitting.

    Args:
        hidden_size: Input dimension (768)
        n_boolean_features: Number of boolean metadata features (10)
        n_numerical_features: Number of numerical metadata features (2)
    """

    def __init__(self, hidden_size: int, n_boolean_features: int = 10, n_numerical_features: int = 2):
        super().__init__()

        # Boolean predictions (hasData, hasDbCrossReferences, etc.)
        self.boolean_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, n_boolean_features)
        )

        # Numerical predictions (log_citations, years_since_pub)
        self.numerical_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size // 2, n_numerical_features)
        )

    def forward(self, fused_embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            fused_embedding: [batch_size, hidden_size]

        Returns:
            boolean_logits: [batch_size, n_boolean_features]
            numerical_preds: [batch_size, n_numerical_features]
        """
        boolean_logits = self.boolean_head(fused_embedding)
        numerical_preds = self.numerical_head(fused_embedding)
        return boolean_logits, numerical_preds


class BiomedicalMultiTaskModel(nn.Module):
    """
    Multi-task model for bio-resource classification + NER with metadata integration.

    Architecture Overview:
    1. Shared RoBERTa encoder (can load from TAPT checkpoint)
    2. Metadata projection: 34 features → 768 dims
    3. Post-encoder fusion: text CLS + metadata → fused representation
    4. Classification head: binary resource detection
    5. NER head: BIO tagging with metadata-enhanced tokens
    6. Auxiliary heads: metadata prediction for regularization

    Args:
        model_name_or_path: HuggingFace model name or path to TAPT checkpoint
        n_metadata_features: Number of metadata features (34)
        num_classes: Number of classification classes (2)
        num_ner_labels: Number of NER labels (3: B, I, O)
        n_boolean_features: Number of boolean metadata features (10)
        n_numerical_features: Number of numerical metadata features (2)
        classification_dropout: Dropout for classification head (0.3)
        ner_dropout: Dropout for NER head (0.1)

    Example:
        >>> model = BiomedicalMultiTaskModel(
        ...     model_name_or_path="roberta-base",
        ...     n_metadata_features=34
        ... )
        >>>
        >>> # Forward pass
        >>> outputs = model(
        ...     input_ids=input_ids,
        ...     attention_mask=attention_mask,
        ...     metadata=metadata_features,
        ...     task='classification'
        ... )
    """

    def __init__(
        self,
        model_name_or_path: str = "roberta-base",
        n_metadata_features: int = 28,
        num_classes: int = 2,
        num_ner_labels: int = 3,
        n_boolean_features: int = 10,
        n_numerical_features: int = 2,
        classification_dropout: float = 0.3,
        ner_dropout: float = 0.1
    ):
        super().__init__()

        # Load RoBERTa encoder (shared across all tasks)
        logger.info(f"Loading encoder from: {model_name_or_path}")
        self.config = AutoConfig.from_pretrained(model_name_or_path)
        self.encoder = AutoModel.from_pretrained(model_name_or_path)
        self.hidden_size = self.config.hidden_size

        # Metadata processing
        self.metadata_projection = MetadataProjection(
            n_features=n_metadata_features,
            hidden_size=self.hidden_size,
            dropout=0.1
        )

        # Fusion layer
        self.fusion_layer = FusionLayer(
            hidden_size=self.hidden_size,
            dropout=0.1
        )

        # Task-specific heads
        self.classification_head = ClassificationHead(
            hidden_size=self.hidden_size,
            num_classes=num_classes,
            dropout=classification_dropout
        )

        self.ner_head = NERHead(
            hidden_size=self.hidden_size,
            num_labels=num_ner_labels,
            dropout=ner_dropout
        )

        # Auxiliary heads for regularization
        self.auxiliary_heads = AuxiliaryMetadataHeads(
            hidden_size=self.hidden_size,
            n_boolean_features=n_boolean_features,
            n_numerical_features=n_numerical_features
        )

        self.n_metadata_features = n_metadata_features
        self.num_classes = num_classes
        self.num_ner_labels = num_ner_labels

        logger.info(f"Initialized BiomedicalMultiTaskModel:")
        logger.info(f"  - Encoder: {model_name_or_path}")
        logger.info(f"  - Hidden size: {self.hidden_size}")
        logger.info(f"  - Metadata features: {n_metadata_features}")
        logger.info(f"  - Classification classes: {num_classes}")
        logger.info(f"  - NER labels: {num_ner_labels}")

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        metadata: torch.Tensor,
        task: str = 'classification',
        labels: Optional[torch.Tensor] = None,
        return_auxiliary: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass supporting both classification and NER tasks.

        Args:
            input_ids: [batch_size, seq_len] - Tokenized input
            attention_mask: [batch_size, seq_len] - Attention mask
            metadata: [batch_size, n_metadata_features] - Metadata features
            task: Task type ('classification' or 'ner')
            labels: Ground truth labels (optional, for loss computation)
            return_auxiliary: Whether to compute auxiliary predictions

        Returns:
            Dictionary containing:
                - 'logits': Task-specific logits
                - 'auxiliary_boolean': Auxiliary boolean predictions (if return_auxiliary=True)
                - 'auxiliary_numerical': Auxiliary numerical predictions (if return_auxiliary=True)
                - 'cls_embedding': CLS token embedding (for analysis)
                - 'metadata_embedding': Projected metadata (for analysis)
                - 'fused_embedding': Fused representation (for analysis)
        """
        # Encode text through shared RoBERTa encoder
        encoder_outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )

        # Extract representations
        sequence_output = encoder_outputs.last_hidden_state  # [batch_size, seq_len, hidden_size]
        cls_embedding = sequence_output[:, 0, :]  # [batch_size, hidden_size]

        # Project metadata
        metadata_embedding = self.metadata_projection(metadata)  # [batch_size, hidden_size]

        # Fuse text and metadata
        fused_embedding = self.fusion_layer(cls_embedding, metadata_embedding)  # [batch_size, hidden_size]

        outputs = {
            'cls_embedding': cls_embedding,
            'metadata_embedding': metadata_embedding,
            'fused_embedding': fused_embedding
        }

        # Task-specific forward pass
        if task == 'classification':
            logits = self.classification_head(fused_embedding)
            outputs['logits'] = logits

        elif task == 'ner':
            logits = self.ner_head(sequence_output, metadata_embedding)
            outputs['logits'] = logits

        else:
            raise ValueError(f"Unknown task: {task}. Must be 'classification' or 'ner'")

        # Auxiliary predictions (for regularization)
        if return_auxiliary:
            boolean_logits, numerical_preds = self.auxiliary_heads(fused_embedding)
            outputs['auxiliary_boolean'] = boolean_logits
            outputs['auxiliary_numerical'] = numerical_preds

        return outputs

    def get_encoder_parameters(self):
        """Get parameters of the shared encoder (for separate learning rate)."""
        return self.encoder.parameters()

    def get_task_head_parameters(self):
        """Get parameters of task-specific heads (for separate learning rate)."""
        params = []
        params.extend(self.classification_head.parameters())
        params.extend(self.ner_head.parameters())
        return params

    def get_metadata_parameters(self):
        """Get parameters of metadata processing layers."""
        params = []
        params.extend(self.metadata_projection.parameters())
        params.extend(self.fusion_layer.parameters())
        return params

    def freeze_encoder(self):
        """Freeze encoder parameters (useful for debugging or quick experiments)."""
        for param in self.encoder.parameters():
            param.requires_grad = False
        logger.info("Encoder parameters frozen")

    def unfreeze_encoder(self):
        """Unfreeze encoder parameters."""
        for param in self.encoder.parameters():
            param.requires_grad = True
        logger.info("Encoder parameters unfrozen")

    def save_pretrained(self, save_directory: str):
        """Save model to directory."""
        import os
        os.makedirs(save_directory, exist_ok=True)
        torch.save(self.state_dict(), os.path.join(save_directory, "pytorch_model.bin"))
        self.config.save_pretrained(save_directory)
        logger.info(f"Model saved to {save_directory}")

    def load_pretrained(self, load_directory: str):
        """Load model from directory."""
        import os
        state_dict = torch.load(os.path.join(load_directory, "pytorch_model.bin"))
        self.load_state_dict(state_dict)
        logger.info(f"Model loaded from {load_directory}")


def create_model(config: dict) -> BiomedicalMultiTaskModel:
    """
    Factory function to create model from configuration.

    Args:
        config: Configuration dictionary with model parameters

    Returns:
        Initialized BiomedicalMultiTaskModel

    Example:
        >>> config = {
        ...     'model_name_or_path': 'roberta-base',
        ...     'n_metadata_features': 34,
        ...     'num_classes': 2,
        ...     'num_ner_labels': 3
        ... }
        >>> model = create_model(config)
    """
    return BiomedicalMultiTaskModel(
        model_name_or_path=config.get('model_name_or_path', 'roberta-base'),
        n_metadata_features=config.get('n_metadata_features', 34),
        num_classes=config.get('num_classes', 2),
        num_ner_labels=config.get('num_ner_labels', 3),
        n_boolean_features=config.get('n_boolean_features', 10),
        n_numerical_features=config.get('n_numerical_features', 2),
        classification_dropout=config.get('classification_dropout', 0.3),
        ner_dropout=config.get('ner_dropout', 0.1)
    )


if __name__ == "__main__":
    # Test model creation
    logging.basicConfig(level=logging.INFO)

    model = BiomedicalMultiTaskModel(model_name_or_path="roberta-base")

    # Test forward pass
    batch_size = 4
    seq_len = 128

    input_ids = torch.randint(0, 1000, (batch_size, seq_len))
    attention_mask = torch.ones(batch_size, seq_len)
    metadata = torch.randn(batch_size, 34)

    # Test classification
    outputs = model(input_ids, attention_mask, metadata, task='classification')
    print(f"Classification logits shape: {outputs['logits'].shape}")  # [4, 2]

    # Test NER
    outputs = model(input_ids, attention_mask, metadata, task='ner')
    print(f"NER logits shape: {outputs['logits'].shape}")  # [4, 128, 3]

    print("\nModel architecture test passed!")
