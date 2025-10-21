# Machine Learning Training Pipeline Explanation

## Overview

This document provides a comprehensive explanation of how the biodata inventory machine learning training pipeline works. The pipeline consists of two main components: **Classification** (identifying bio-resource papers) and **Named Entity Recognition (NER)** (extracting database names from text).

## Table of Contents

1. [Data Structure & Labels](#data-structure--labels)
2. [Data Splitting Process](#data-splitting-process)
3. [Classification Training](#classification-training)
4. [Named Entity Recognition (NER) Training](#named-entity-recognition-ner-training)
5. [BIO Tagging Scheme (Detailed)](#bio-tagging-scheme-detailed)
6. [Training Process](#training-process)
7. [Model Architecture](#model-architecture)
8. [Evaluation & Model Selection](#evaluation--model-selection)

---

## Data Structure & Labels

### Classification Data (`manual_classifications.csv`)

The classification task aims to identify whether a scientific paper describes a biological database or resource.

```csv
id,title,abstract,curation_score
123,"Database of protein structures","This paper describes a comprehensive database of...",1
456,"Statistical analysis methods","This study presents novel statistical methods for...",0
789,"UniProt: protein sequence database","UniProt provides a comprehensive resource for...",1
```

**Label Definition:**
- **`curation_score = "1"`**: **Positive** (paper describes a bio-resource/database)
- **`curation_score = "0"`**: **Negative** (paper does not describe a bio-resource)

**Manual Curation Process:**
Domain experts manually read scientific papers and made binary decisions based on criteria such as:
- Does the paper describe a biological database?
- Does it present a computational resource for biological data?
- Is it introducing a new tool for biological research?

**Examples:**
- ✅ **Positive**: "UniProt: a comprehensive resource for protein sequence and annotation data"
- ✅ **Positive**: "PDB: the Protein Data Bank for macromolecular structure data"
- ❌ **Negative**: "Statistical methods for analyzing gene expression data"
- ❌ **Negative**: "A case study of protein folding in laboratory conditions"

### NER Data (`manual_ner_extraction.csv`)

The NER task extracts database names from scientific text, identifying two types of entities:

```csv
id,title,abstract,compound_name,full_name
123,"Database study","Text contains PDB and Protein Data Bank references","PDB,UniProt","Protein Data Bank,Universal Protein Resource"
456,"Analysis paper","Using Gene Ontology for classification","GO","Gene Ontology"
```

**Entity Types:**
- **`compound_name`** → **COM** entities (abbreviations, short names)
  - Examples: "PDB", "UniProt", "GO", "NCBI"
- **`full_name`** → **FUL** entities (complete descriptive names)  
  - Examples: "Protein Data Bank", "Universal Protein Resource", "Gene Ontology"

---

## Data Splitting Process

### Classification Data Splitting (`src/class_data_generator.py`)

```python
def split_classification_data():
    # 1. Load and clean data
    df = pd.read_csv('manual_classifications.csv', dtype=str)
    
    # 2. Filter to only certain labels (removes uncertain annotations)
    df = df[df['curation_score'].isin(['0', '1'])]
    
    # 3. Check data integrity
    assert df['id'].count() == df['id'].nunique()  # No duplicate IDs
    
    # 4. Split into train/validation/test (70%/15%/15%)
    train, val_test = train_test_split(
        df, 
        test_size=0.3,
        random_state=241,  # Reproducible splits
        stratify=df['curation_score']  # Maintain class balance
    )
    
    val, test = train_test_split(
        val_test,
        test_size=0.5,  # 50% of 30% = 15% overall
        random_state=241,
        stratify=val_test['curation_score']
    )
    
    # 5. Save splits
    train.to_csv('train_paper_classif.csv', index=False)
    val.to_csv('val_paper_classif.csv', index=False)
    test.to_csv('test_paper_classif.csv', index=False)
```

**Key Features:**
- **Stratified splitting**: Maintains proportion of positive/negative examples in each split
- **Reproducible**: Fixed random seed ensures consistent splits across runs
- **Data validation**: Checks for duplicate IDs and data integrity

### NER Data Splitting (`src/ner_data_generator.py`)

The NER data splitting is more complex due to the need for BIO tagging:

```python
def split_ner_data():
    # 1. Load manual annotations
    df = pd.read_csv('manual_ner_extraction.csv', dtype=str)
    
    # 2. Convert to BIO tagging scheme
    df = BIO_scheme_transform(df)
    
    # 3. Split data (70%/15%/15%)
    train, val, test = split_df(df, seed=True, splits=[0.7, 0.15, 0.15])
    
    # 4. Save as both CSV and pickle formats
    train.to_csv('train_ner.csv', index=False)
    train.to_pickle('train_ner.pkl')  # Preserves data types
    
    val.to_csv('val_ner.csv', index=False)
    val.to_pickle('val_ner.pkl')
    
    test.to_csv('test_ner.csv', index=False)
    test.to_pickle('test_ner.pkl')
```

---

## Classification Training

### Overview
The classification model learns to distinguish between papers that describe biological databases/resources versus general scientific papers.

### Architecture
```python
# Load pre-trained biomedical RoBERTa model
model = AutoModelForSequenceClassification.from_pretrained(
    "allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500",
    num_labels=2  # Binary classification: bio-resource vs not
)
```

### Training Process (`src/class_train.py`)

```python
def train_classification_model():
    # 1. Data preprocessing
    def preprocess_text(title, abstract):
        # Concatenate title and abstract with period separator
        text = add_period(title) + " " + abstract
        
        # Tokenize and truncate to max length
        inputs = tokenizer(
            text,
            max_length=256,
            truncation=True,
            padding=True,
            return_tensors="pt"
        )
        return inputs
    
    # 2. Training loop
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch in train_dataloader:
            # Forward pass
            outputs = model(
                input_ids=batch['input_ids'],
                attention_mask=batch['attention_mask'],
                labels=batch['labels']
            )
            
            loss = outputs.loss
            
            # Backward pass
            loss.backward()
            optimizer.step()
            scheduler.step()  # Learning rate scheduling
            optimizer.zero_grad()
            
            total_loss += loss.item()
        
        # 3. Validation evaluation
        val_metrics = evaluate_on_validation(model, val_dataloader)
        
        # 4. Save best model based on validation performance
        if val_metrics['precision'] > best_precision:
            best_precision = val_metrics['precision']
            save_model(model, tokenizer, output_dir)
```

### Input Processing
```python
# Example input transformation:
title = "UniProt: a comprehensive resource for protein sequence"
abstract = "UniProt provides a comprehensive, high-quality..."

# Combined input to model:
input_text = "UniProt: a comprehensive resource for protein sequence. UniProt provides a comprehensive, high-quality..."

# Tokenized:
tokens = ["[CLS]", "Uni", "Prot", ":", "a", "comprehensive", ..., "[SEP]"]
token_ids = [101, 8362, 18093, 12334, 9, 2828, ...]  # Numerical representation
```

### Loss Function
```python
# Binary cross-entropy loss
def compute_loss(logits, labels):
    """
    logits: [batch_size, 2] - model predictions
    labels: [batch_size] - true labels (0 or 1)
    """
    loss_fn = nn.CrossEntropyLoss()
    return loss_fn(logits, labels)

# Example:
# logits = [[0.2, 0.8], [-0.5, 0.3]]  # Batch of 2, class probabilities
# labels = [1, 0]                      # True labels
# loss = cross_entropy(logits, labels)
```

---

## Named Entity Recognition (NER) Training

### Overview
The NER model extracts database names from scientific text, identifying both abbreviations (COM) and full names (FUL).

---

## BIO Tagging Scheme (Detailed)

### What is BIO Tagging?

**BIO** stands for **B**eginning, **I**nside, **O**utside. It's a sequence labeling scheme that marks the boundaries of entities in text.

### Complete Tag Set
```
O      = Outside (not part of any entity)
B-COM  = Beginning of Compound/Common name (abbreviation)
I-COM  = Inside/Continuation of Compound name
B-FUL  = Beginning of Full name (complete name)
I-FUL  = Inside/Continuation of Full name
```

### Why Use BIO Tagging?

**Problem**: How do you mark multi-word entities in a sequence?

```
❌ Simple approach: 
Text: "Protein Data Bank"
Tags:  ENTITY ENTITY ENTITY  # Can't distinguish from 3 separate entities

✅ BIO approach:
Text: "Protein Data Bank" 
Tags:  B-FUL  I-FUL I-FUL   # Clearly one entity with proper boundaries
```

### Detailed Examples

#### Example 1: Simple entities
```
Text: "PDB contains protein structures"
Words: ["PDB", "contains", "protein", "structures"]
Tags:  [B-COM,    O,         O,         O        ]

Interpretation: "PDB" is a compound name entity
```

#### Example 2: Multi-word entities
```
Text: "The Protein Data Bank contains structures"
Words: ["The", "Protein", "Data", "Bank", "contains", "structures"]
Tags:  [ O,     B-FUL,   I-FUL,  I-FUL,     O,          O        ]

Interpretation: "Protein Data Bank" is one full name entity
```

#### Example 3: Multiple entities
```
Text: "PDB and UniProt are popular databases"
Words: ["PDB", "and", "UniProt", "are", "popular", "databases"]
Tags:  [B-COM,  O,     B-COM,     O,       O,         O       ]

Interpretation: Two separate compound name entities
```

#### Example 4: Adjacent entities (why BIO is crucial)
```
Text: "PDB UniProt databases"
Words: ["PDB", "UniProt", "databases"] 
Tags:  [B-COM,  B-COM,      O        ]

Without BIO: Might think "PDB UniProt" is one entity
With BIO: Clearly identifies two separate entities
```

#### Example 5: Complex real-world sentence
```
Text: "The Protein Data Bank (PDB) and Gene Ontology database provide resources"
Words: ["The", "Protein", "Data", "Bank", "(", "PDB", ")", "and", "Gene", "Ontology", "database", "provide", "resources"]
Tags:  [ O,     B-FUL,   I-FUL,  I-FUL,  O,   B-COM,  O,    O,    B-FUL,  I-FUL,      O,         O,        O      ]

Interpretation: 
- "Protein Data Bank" (full name)
- "PDB" (compound name) 
- "Gene Ontology" (full name)
```

#### Example 6: Embedded entities
```
Text: "GenBank database from NCBI"
Words: ["GenBank", "database", "from", "NCBI"]
Tags:  [ B-COM,     O,          O,      B-COM ]

Interpretation: Two separate compound entities
```

### BIO Tagging Conversion Process

#### Step 1: Manual Annotation
```
Original text: "We used the Protein Data Bank and PDB for analysis"

Human annotations:
- Span (15-31): "Protein Data Bank" → Full name
- Span (36-39): "PDB" → Compound name
```

#### Step 2: Tokenization
```python
tokens = tokenizer.tokenize(text)
# Result: ["We", "used", "the", "Protein", "Data", "Bank", "and", "PDB", "for", "analysis"]
```

#### Step 3: Align annotations with tokens
```python
def align_annotations_with_tokens(tokens, annotations):
    labels = ["O"] * len(tokens)  # Initialize all as Outside
    
    for annotation in annotations:
        start_token, end_token = find_token_span(annotation.span)
        entity_type = annotation.type  # "FUL" or "COM"
        
        # Set first token as Beginning
        labels[start_token] = f"B-{entity_type}"
        
        # Set remaining tokens as Inside
        for i in range(start_token + 1, end_token):
            labels[i] = f"I-{entity_type}"
    
    return labels

# Result: ["O", "O", "O", "B-FUL", "I-FUL", "I-FUL", "O", "B-COM", "O", "O"]
```

#### Step 4: Numerical conversion for training
```python
NER_TAG2ID = {
    'O': 0,
    'B-COM': 1, 
    'I-COM': 2,
    'B-FUL': 3,
    'I-FUL': 4
}

numerical_labels = [0, 0, 0, 3, 4, 4, 0, 1, 0, 0]
```

### Common BIO Tagging Challenges

#### Challenge 1: Subword tokenization
```
Text: "UniProt database"
Subword tokens: ["Uni", "Prot", "database"]
Labels: [B-COM, I-COM, O]

# The tokenizer splits "UniProt" into subwords, but they're still part of one entity
```

#### Challenge 2: Nested or overlapping entities
```
Text: "The Protein Data Bank (PDB)"
# Two ways to interpret:
# Option 1: Two separate entities
Labels: [O, B-FUL, I-FUL, I-FUL, O, B-COM, O]

# Option 2: One entity with alias (current approach)
# We treat these as separate entities for simplicity
```

#### Challenge 3: Partial entities
```
Text: "PDB-like databases"
# Is "PDB-like" an entity or just an adjective?
# Current approach: Mark "PDB" as B-COM, ignore "-like"
Labels: [B-COM, O, O]
```

---

## Training Process

### NER Training Loop (`src/ner_train.py`)

```python
def train_ner_model():
    # 1. Load pre-trained model
    model = AutoModelForTokenClassification.from_pretrained(
        "allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500",
        num_labels=5  # O, B-COM, I-COM, B-FUL, I-FUL
    )
    
    # 2. Prepare data
    def tokenize_and_align_labels(examples):
        tokenized_inputs = tokenizer(
            examples['tokens'],
            truncation=True,
            is_split_into_words=True,  # Input is pre-tokenized
            padding=True
        )
        
        # Align labels with subword tokens
        labels = []
        for i, label in enumerate(examples['ner_tags']):
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            aligned_labels = align_labels_with_tokens(label, word_ids)
            labels.append(aligned_labels)
            
        tokenized_inputs["labels"] = labels
        return tokenized_inputs
    
    # 3. Training loop
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        
        for batch in train_dataloader:
            # Forward pass
            outputs = model(**batch)
            loss = outputs.loss
            
            # Backward pass  
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            
            total_loss += loss.item()
        
        # 4. Validation
        val_metrics = evaluate_ner_model(model, val_dataloader)
        
        # 5. Save best model
        if val_metrics['f1'] > best_f1:
            best_f1 = val_metrics['f1']
            save_model(model, output_dir)
```

### Token-Level Prediction Process

```python
def predict_entities(text):
    # 1. Tokenize input
    tokens = tokenizer.tokenize(text)
    input_ids = tokenizer.convert_tokens_to_ids(tokens)
    
    # 2. Model prediction
    with torch.no_grad():
        outputs = model(torch.tensor([input_ids]))
        predictions = torch.argmax(outputs.logits, dim=-1)
    
    # 3. Convert predictions to labels
    predicted_labels = [ID2NER_TAG[pred.item()] for pred in predictions[0]]
    
    # 4. Extract entities
    entities = extract_entities_from_bio_tags(tokens, predicted_labels)
    
    return entities

# Example:
text = "The Protein Data Bank contains structures"
entities = predict_entities(text)
# Result: [("Protein Data Bank", "FUL", (1, 4))]
```

### Entity Extraction from BIO Tags

```python
def extract_entities_from_bio_tags(tokens, bio_tags):
    entities = []
    current_entity = None
    
    for i, (token, tag) in enumerate(zip(tokens, bio_tags)):
        if tag.startswith('B-'):  # Beginning of entity
            # Save previous entity if exists
            if current_entity:
                entities.append(current_entity)
            
            # Start new entity
            entity_type = tag[2:]  # Remove 'B-' prefix
            current_entity = {
                'text': token,
                'type': entity_type,
                'start': i,
                'end': i + 1
            }
            
        elif tag.startswith('I-') and current_entity:  # Inside entity
            current_entity['text'] += f" {token}"
            current_entity['end'] = i + 1
            
        else:  # Outside entity
            if current_entity:
                entities.append(current_entity)
                current_entity = None
    
    # Don't forget last entity
    if current_entity:
        entities.append(current_entity)
    
    return entities
```

---

## Model Architecture

### Base Model: BioBERT/RoBERTa

Both classification and NER models are built on top of:
```
allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500
```

This is a **domain-adapted RoBERTa model** that has been:
1. **Pre-trained** on general text (books, Wikipedia, etc.)
2. **Domain-adapted** on biomedical literature
3. **Task-adapted** on biomedical text classification tasks

### Architecture Details

#### Classification Model
```python
class BioResourceClassifier(nn.Module):
    def __init__(self):
        self.roberta = RobertaModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(768, 2)  # 768 = hidden size, 2 = classes
    
    def forward(self, input_ids, attention_mask):
        # Get contextualized embeddings
        outputs = self.roberta(input_ids, attention_mask)
        
        # Use [CLS] token representation for classification
        pooled_output = outputs.pooler_output  # [batch_size, 768]
        
        # Apply dropout and classify
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)  # [batch_size, 2]
        
        return logits
```

#### NER Model  
```python
class BioNERModel(nn.Module):
    def __init__(self):
        self.roberta = RobertaModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(768, 5)  # 5 = number of NER tags
    
    def forward(self, input_ids, attention_mask):
        # Get token-level embeddings
        outputs = self.roberta(input_ids, attention_mask)
        sequence_output = outputs.last_hidden_state  # [batch_size, seq_len, 768]
        
        # Apply dropout and classify each token
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)  # [batch_size, seq_len, 5]
        
        return logits
```

### Key Differences

| Aspect | Classification | NER |
|--------|---------------|-----|
| **Output** | Single prediction per text | Prediction per token |
| **Architecture** | Uses [CLS] token | Uses all token embeddings |
| **Classes** | 2 (bio-resource vs not) | 5 (O, B-COM, I-COM, B-FUL, I-FUL) |
| **Loss** | Cross-entropy | Token-level cross-entropy |

---

## Evaluation & Model Selection

### Classification Metrics

```python
def compute_classification_metrics(model, dataloader):
    all_predictions = []
    all_labels = []
    
    for batch in dataloader:
        with torch.no_grad():
            outputs = model(**batch)
            predictions = torch.argmax(outputs.logits, dim=-1)
            
        all_predictions.extend(predictions.cpu().numpy())
        all_labels.extend(batch['labels'].cpu().numpy())
    
    # Calculate metrics
    precision = precision_score(all_labels, all_predictions)
    recall = recall_score(all_labels, all_predictions)
    f1 = f1_score(all_labels, all_predictions)
    
    return {
        'precision': precision,
        'recall': recall, 
        'f1': f1
    }
```

**Model Selection**: Best model chosen based on **validation precision** (minimizes false positives)

### NER Metrics

```python
def compute_ner_metrics(model, dataloader):
    all_predictions = []
    all_labels = []
    
    for batch in dataloader:
        with torch.no_grad():
            outputs = model(**batch)
            predictions = torch.argmax(outputs.logits, dim=-1)
        
        # Convert to BIO tags for evaluation
        for i in range(len(predictions)):
            pred_labels = [ID2NER_TAG[p.item()] for p in predictions[i]]
            true_labels = [ID2NER_TAG[l.item()] for l in batch['labels'][i]]
            
            all_predictions.append(pred_labels)
            all_labels.append(true_labels)
    
    # Entity-level evaluation using seqeval
    from seqeval.metrics import f1_score, precision_score, recall_score
    
    return {
        'precision': precision_score(all_labels, all_predictions),
        'recall': recall_score(all_labels, all_predictions),
        'f1': f1_score(all_labels, all_predictions)
    }
```

**Model Selection**: Best model chosen based on **validation F1-score** (balances precision and recall)

### Why Entity-Level Evaluation?

```python
# Example showing why entity-level evaluation matters

# Prediction 1: Token-level accuracy = 80%
true_labels = ["O", "B-FUL", "I-FUL", "I-FUL", "O"]
pred_labels = ["O", "B-FUL", "I-FUL", "O", "O"]  # 4/5 correct tokens

# But entity-level: 0% F1 (predicted "Protein Data" vs true "Protein Data Bank")

# Prediction 2: Token-level accuracy = 60% 
true_labels = ["O", "B-FUL", "I-FUL", "I-FUL", "O"]
pred_labels = ["B-FUL", "I-FUL", "I-FUL", "I-FUL", "O"]  # 3/5 correct tokens

# But entity-level: 100% F1 (extracted "Protein Data Bank" correctly, just wrong boundary)
```

Entity-level evaluation ensures the model learns to extract complete, meaningful entities rather than just individual tokens.

### Training Hyperparameters

#### Classification
```python
HYPERPARAMETERS = {
    'learning_rate': 2e-5,      # Standard for fine-tuning transformers
    'batch_size': 16,           # Balanced for memory/performance  
    'num_epochs': 10,           # Sufficient for convergence
    'weight_decay': 0.0,        # No L2 regularization by default
    'max_length': 256,          # Truncate long texts
    'warmup_steps': 0.1 * total_steps,  # Linear warmup
}
```

#### NER
```python  
HYPERPARAMETERS = {
    'learning_rate': 2e-5,
    'batch_size': 16,
    'num_epochs': 10,
    'weight_decay': 0.0,
    'max_length': 512,          # Longer sequences for NER
    'label_smoothing': 0.0,     # No label smoothing
}
```

### Model Checkpointing & Selection

```python
def training_loop_with_checkpointing():
    best_metric = 0.0
    
    for epoch in range(num_epochs):
        # Training phase
        train_loss = train_one_epoch(model, train_dataloader)
        
        # Validation phase
        val_metrics = evaluate(model, val_dataloader)
        
        # Save best model
        current_metric = val_metrics['precision']  # or 'f1' for NER
        if current_metric > best_metric:
            best_metric = current_metric
            
            # Save complete checkpoint
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_metric': best_metric,
                'metrics': val_metrics
            }, f'{output_dir}/checkpt.pt')
            
            # Save training statistics
            save_train_stats(train_losses, val_metrics, output_dir)
```

---

## Summary

This training pipeline creates two complementary models:

1. **Classification Model**: Identifies papers that describe biological databases/resources
   - Input: Paper title + abstract
   - Output: Binary prediction (bio-resource vs not)
   - Evaluation: Precision-focused (minimize false positives)

2. **NER Model**: Extracts database names from scientific text
   - Input: Text tokens
   - Output: BIO tags for each token
   - Evaluation: Entity-level F1-score
   - Entities: Compound names (abbreviations) and Full names

Both models use domain-adapted biomedical language models and are trained on manually curated datasets. The BIO tagging scheme ensures proper handling of multi-word entities and entity boundaries in the NER task.

The trained models work together in the full pipeline: the classification model filters relevant papers, and the NER model extracts database names from those papers to build a comprehensive inventory of biological resources.