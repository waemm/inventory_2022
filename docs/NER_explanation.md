# Named Entity Recognition (NER) for Biodata Resources

**Purpose**: Extract specific database and resource names from scientific paper abstracts
**Last Updated**: 2025-10-31
**Performance**: V1 achieves 0.918 F1 (excellent, +16.8% over BERT baseline)

---

## Table of Contents

1. [What is NER?](#what-is-ner)
2. [How NER Works](#how-ner-works)
3. [What to Extract](#what-to-extract)
4. [What NOT to Extract](#what-not-to-extract)
5. [Output Format](#output-format)
6. [Quality Guidelines](#quality-guidelines)
7. [Examples](#examples)
8. [Performance Metrics](#performance-metrics)
9. [Evaluation Approach](#evaluation-approach)

---

## What is NER?

**Named Entity Recognition (NER)** is the task of identifying and extracting specific entity names from text.

### In This Project

**Task**: Extract **specific biodata resource names** (databases, repositories, tools) from scientific paper abstracts

**Input**: Paper title + abstract text

**Output**: JSON array of database/resource names

**Example**:
```
Input: "We deposited RNA-seq data in GEO and analyzed with KEGG pathways."
Output: ["GEO", "KEGG"]
```

### Why NER Matters

- **Inventory Building**: Identifies which databases are mentioned in scientific literature
- **Resource Discovery**: Finds new and updated biodata resources
- **Literature Mining**: Links papers to the resources they use or describe
- **Trend Analysis**: Tracks database usage over time

---

## How NER Works

### Process Overview

1. **Read Input**: Title + abstract text
2. **Scan for Resource Names**: Look for specific database/tool names
3. **Extract Names**: Capture exact names as they appear
4. **Handle Variants**: Extract both acronyms and full names
5. **Output JSON Array**: Return list of extracted names

### Context Clues for NER

Look for these phrases that often precede database names:

**Deposit/Storage:**
- "deposited in [NAME]"
- "submitted to [NAME]"
- "available at [NAME]"
- "stored in [NAME]"

**Retrieval/Access:**
- "obtained from [NAME]"
- "retrieved from [NAME]"
- "downloaded from [NAME]"
- "accessed from [NAME]"

**Usage/Analysis:**
- "using [NAME]"
- "analyzed with [NAME]"
- "annotated with [NAME]"
- "according to [NAME]"

**Introduction/Description:**
- "we present [NAME]"
- "we introduce [NAME]"
- "[NAME] is a database/tool for..."
- "[NAME] is available at http://..."

### Name Patterns to Recognize

**Acronyms in Parentheses:**
- "Gene Expression Omnibus (GEO)" → Extract both
- "Protein Data Bank (PDB)" → Extract both
- "NCBI Reference Sequence (RefSeq)" → Extract both

**URL Mentions:**
- "available at http://www.genbank.org/" → Extract GenBank
- "accessible at blast.ncbi.nlm.nih.gov" → Extract BLAST

**Title Format:**
- "GenBank: a database for nucleotide sequences" → Extract GenBank
- "BLAST: Basic Local Alignment Search Tool" → Extract BLAST

**Version Numbers:**
- "UniProt version 2.0" → Extract "UniProt" or "UniProt 2.0"
- "ArachnoServer 3.0" → Extract "ArachnoServer 3.0"

---

## What to Extract

### Biodata Resources to Extract ✅

**1. Biological Databases**
- Sequence databases: GenBank, EMBL, DDBJ, RefSeq
- Protein databases: UniProt, Swiss-Prot, TrEMBL
- Structure databases: PDB (Protein Data Bank), SCOP, CATH
- Genome databases: Ensembl, UCSC Genome Browser

**2. Data Repositories**
- Expression data: GEO (Gene Expression Omnibus), ArrayExpress
- Sequencing data: SRA (Sequence Read Archive), ENA
- Proteomics: PRIDE, ProteomeXchange, MassIVE
- Metabolomics: MetaboLights, Metabolomics Workbench

**3. Bioinformatics Tools/Platforms**
- Alignment tools: BLAST, Clustal, MUSCLE
- Analysis platforms: Galaxy, Cytoscape
- Visualization tools: IGV, JBrowse
- Web servers: ExPASy, NCBI tools

**4. Ontologies & Knowledge Bases**
- Gene Ontology (GO)
- KEGG (Kyoto Encyclopedia of Genes and Genomes)
- Reactome
- WikiPathways
- Disease Ontology

**5. Specialized Resources**
- Species-specific: FlyBase, WormBase, TAIR, MGI
- Disease-specific: ClinVar, OMIM, Cancer Genome Atlas
- Interaction databases: STRING, BioGRID, IntAct
- Pathway databases: Pathway Commons, BioCyc

**6. Custom/Novel Resources**
- Any newly introduced database mentioned in the paper
- Updated versions of existing databases
- Specialized domain-specific resources

---

## What NOT to Extract

### Exclude These ❌

**1. Programming Languages & General Software**
- Python, R, Java, C++, JavaScript, Perl
- Excel, SPSS, SAS, GraphPad Prism
- Matlab, Mathematica

**2. Software Libraries & Packages**
- pandas, NumPy, scikit-learn, TensorFlow
- Bioconductor packages (unless specifically a database)
- R packages (unless specifically a database)

**3. Laboratory Methods & Protocols**
- PCR, qPCR, RT-PCR
- ELISA, Western blot, immunoassay
- Flow cytometry, microscopy
- DNA sequencing methods (Sanger, Illumina, etc.)

**4. Statistical & Machine Learning Methods**
- PCA (Principal Component Analysis)
- t-test, ANOVA, chi-square
- Linear regression, logistic regression
- Clustering, classification algorithms
- Deep learning, neural networks

**5. Generic Terms Without Specific Names**
- "database" (without specific name)
- "tool" (without specific name)
- "repository" (without specific name)
- "server" (without specific name)
- "resource" (without specific name)
- "software" (without specific name)

**6. Hardware & Equipment**
- Sequencing machines
- Mass spectrometers
- Lab equipment
- Computer hardware

**7. General Web Services**
- Google, Wikipedia, PubMed (unless paper is about PubMed)
- Generic cloud services (AWS, Azure)
- General collaboration tools

---

## Output Format

### JSON Array Format

**Structure**: List of strings, each representing a database/resource name

**Basic Example**:
```json
["GenBank", "PDB", "UniProt"]
```

**Empty Result** (no databases found):
```json
[]
```

### CSV Format (for batch processing)

**Column**: `databases`
**Format**: JSON array as escaped string

**Examples**:
```csv
paper_id,has_bioresource,databases,confidence
33156326,true,"[""MetaNetX""]",high
22135301,true,"[""BacMap""]",high
28698795,true,"[""MPC"", ""Modular Program Constructor""]",high
23846595,false,"[]",high
```

**Important CSV Escaping**:
- Wrap entire JSON array in double quotes: `"[...]"`
- Escape inner quotes: `[""Name""]` not `["Name"]`
- Empty array: `"[]"` (with outer quotes)

### Complete Output (Classification + NER)

**Format**: JSON object with classification and NER combined

```json
{
  "has_bioresource": true,
  "databases": ["GenBank", "PDB", "UniProt"],
  "confidence": "high"
}
```

**Fields**:
- `has_bioresource`: Boolean (true if paper mentions databases)
- `databases`: Array of extracted names (empty if no databases)
- `confidence`: String ("high", "medium", or "low")

---

## Quality Guidelines

### 1. Acronym Handling ✅

**Rule**: Extract BOTH the acronym AND full name when provided

**Examples**:
```
Input: "Gene Expression Omnibus (GEO)"
Output: ["Gene Expression Omnibus", "GEO"]

Input: "Protein Data Bank (PDB)"
Output: ["Protein Data Bank", "PDB"]

Input: "NCBI Reference Sequence (RefSeq)"
Output: ["NCBI Reference Sequence", "RefSeq"]
```

**Rationale**: Improves recall, allows flexible name matching

---

### 2. Deduplication ✅

**Rule**: Include each unique database name ONCE

**Examples**:
```
Input: "Data from GEO database...analyzed GEO data...deposited in GEO"
Output: ["GEO"]  (not ["GEO", "GEO", "GEO"])

Input: "GenBank and NCBI GenBank accession..."
Output: ["GenBank"]  (deduplicate)
```

**Rationale**: Avoid inflating extraction counts

---

### 3. Name Normalization ⚠️

**Rule**: Extract names AS THEY APPEAR in text (don't normalize during extraction)

**Examples**:
```
Input: "Gene Expression Omnibus (GEO)"
Output: ["Gene Expression Omnibus", "GEO"]
NOT: ["gene expression omnibus", "geo"]  (preserve case)

Input: "PDB database"
Output: ["PDB"]
NOT: ["Protein Data Bank"]  (don't expand if not in text)
```

**Note**: Normalization happens during evaluation, not extraction

---

### 4. Version Numbers 📌

**Rule**: Include version numbers if they're part of the official name

**Examples**:
```
Input: "UniProt version 2024.1"
Output: ["UniProt"] or ["UniProt 2024.1"]  (either acceptable)

Input: "ArachnoServer 3.0"
Output: ["ArachnoServer 3.0"]  (version is part of name)

Input: "GenBank release 256"
Output: ["GenBank"]  (release number not part of name)
```

**Guideline**: Use judgment - if version is emphasized, include it

---

### 5. Multiple Mentions ✅

**Rule**: Extract from BOTH title AND abstract

**Example**:
```
Title: "GEO: Gene Expression Omnibus"
Abstract: "We deposited data in ArrayExpress and analyzed with KEGG."

Output: ["GEO", "Gene Expression Omnibus", "ArrayExpress", "KEGG"]
```

**Don't miss**: Database mentioned only in title or only in abstract

---

### 6. Context Verification ⚠️

**Rule**: Verify the name is actually a biodata resource, not coincidental match

**Ambiguous Examples**:
```
"The GO command in shell script..."
→ NOT Gene Ontology (different context)

"The SRA file format..."
→ Could be Sequence Read Archive (check context)

"STRING analysis revealed..."
→ Could be STRING database OR just word "string" (check context)
```

**Guideline**: Use surrounding context to disambiguate

---

### 7. Confidence Assignment 📊

**High Confidence**:
- Clear, explicit mention with context
- Database name + action phrase ("deposited in", "using", etc.)
- Multiple mentions of same database
- Example: "Data deposited in GenBank under accession..."

**Medium Confidence**:
- Implied mention without explicit context
- Single mention without supporting phrases
- Ambiguous acronym (could mean multiple things)
- Example: "GenBank accession CP123456"

**Low Confidence**:
- Very uncertain or ambiguous
- Possible coincidental name match
- Unusual or unrecognized database name
- Example: "The GO analysis..." (GO = Gene Ontology or "go"?)

---

## Examples

### Example 1: Multiple Databases (High Confidence) ✅

**Input**:
```
Title: "Multi-omics data integration in cancer research"
Abstract: "We deposited RNA-seq data in the Gene Expression Omnibus (GEO)
under accession GSE12345 and protein data in ProteomeXchange. Pathway
analysis was performed using KEGG and protein interactions were analyzed
with STRING database."
```

**NER Output**:
```json
{
  "databases": ["Gene Expression Omnibus", "GEO", "ProteomeXchange", "KEGG", "STRING"],
  "confidence": "high"
}
```

**Extracted**: 5 databases (both acronym and full name for GEO)

---

### Example 2: Repository Deposit (High Confidence) ✅

**Input**:
```
Title: "Genome sequencing of novel bacterial strain"
Abstract: "Complete genome sequences were deposited in GenBank under
accession CP123456 and CP123457. Annotations were obtained from NCBI
RefSeq database."
```

**NER Output**:
```json
{
  "databases": ["GenBank", "NCBI RefSeq"],
  "confidence": "high"
}
```

**Extracted**: 2 databases

---

### Example 3: Tool Usage (High Confidence) ✅

**Input**:
```
Title: "Comparative genomics approach to bacterial evolution"
Abstract: "Sequences were aligned using BLAST and structural predictions
were obtained from the Protein Data Bank (PDB). Orthologous genes were
identified using the EggNOG database."
```

**NER Output**:
```json
{
  "databases": ["BLAST", "Protein Data Bank", "PDB", "EggNOG"],
  "confidence": "high"
}
```

**Extracted**: 4 names (including both PDB forms)

---

### Example 4: NO Databases - Lab Methods (High Confidence) ❌

**Input**:
```
Title: "Inflammatory mechanisms in cardiovascular disease"
Abstract: "We investigated inflammatory markers in patients with heart
disease. Blood samples were collected and analyzed using ELISA and flow
cytometry. Statistical analysis was performed using R software."
```

**NER Output**:
```json
{
  "databases": [],
  "confidence": "high"
}
```

**Extracted**: NONE
**Reason**: ELISA, flow cytometry, R are not biodata resources

---

### Example 5: NO Databases - Software Tools (High Confidence) ❌

**Input**:
```
Title: "Machine learning for clinical prediction"
Abstract: "We developed predictive models using Python and scikit-learn
library. Data were processed with pandas and visualized using matplotlib.
Cross-validation was performed to assess model performance."
```

**NER Output**:
```json
{
  "databases": [],
  "confidence": "high"
}
```

**Extracted**: NONE
**Reason**: Python, scikit-learn, pandas, matplotlib are programming tools, not biodata resources

---

### Example 6: Ontologies and Pathways (High Confidence) ✅

**Input**:
```
Title: "Systems biology approach to disease mechanisms"
Abstract: "Gene sets were annotated using Gene Ontology (GO) and Disease
Ontology. Pathway analysis was conducted using Reactome and WikiPathways
databases."
```

**NER Output**:
```json
{
  "databases": ["Gene Ontology", "GO", "Disease Ontology", "Reactome", "WikiPathways"],
  "confidence": "high"
}
```

**Extracted**: 5 names (ontologies and pathway databases)

---

### Example 7: Mixed Content (Medium Confidence) ⚠️

**Input**:
```
Title: "Genomic analysis of antibiotic resistance"
Abstract: "Sequences were obtained from GenBank and analyzed using Python
scripts. Statistical analysis was performed using R. Results were compared
with KEGG pathway annotations."
```

**NER Output**:
```json
{
  "databases": ["GenBank", "KEGG"],
  "confidence": "medium"
}
```

**Extracted**: 2 databases (GenBank, KEGG)
**NOT extracted**: Python, R (programming languages)

---

### Example 8: Title-Only Mention (High Confidence) ✅

**Input**:
```
Title: "BacMap: bacterial genome atlas"
Abstract: "We developed a comprehensive resource for visualizing bacterial
genomes with integrated annotations and comparative features. The platform
is freely available online."
```

**NER Output**:
```json
{
  "databases": ["BacMap"],
  "confidence": "high"
}
```

**Extracted**: 1 database (from title, paper introduces BacMap)

---

### Example 9: Ambiguous Acronym (Low Confidence) ⚠️

**Input**:
```
Title: "GO analysis reveals functional enrichment"
Abstract: "We performed GO analysis to identify enriched terms. The GO
approach revealed significant pathways."
```

**NER Output**:
```json
{
  "databases": ["GO"],
  "confidence": "low"
}
```

**Extracted**: GO (likely Gene Ontology, but "go" could be verb)
**Reason**: Ambiguous context, low confidence

---

### Example 10: Version Number Included (High Confidence) ✅

**Input**:
```
Title: "UniProt: comprehensive protein resource"
Abstract: "We describe version 2024.1 of UniProt, the Universal Protein
Resource, with enhanced annotations and cross-references."
```

**NER Output**:
```json
{
  "databases": ["UniProt", "Universal Protein Resource"],
  "confidence": "high"
}
```

**Extracted**: 2 names (short + full form)
**Note**: Version number optional to include

---

## Performance Metrics

### V1 NER Performance (Claude Sonnet)

**From Analysis**: `data/llm_comparison/results/ANALYSIS_SUMMARY.md`

| Metric | Score | Interpretation |
|--------|-------|----------------|
| **Precision** | 0.899 | 90% of extracted names are correct |
| **Recall** | 0.937 | Catches 94% of actual database names |
| **F1 Score** | **0.918** | Excellent overall performance |

**Comparison to BERT Baseline**:
- BERT NER F1: 0.749
- Sonnet NER F1: 0.918
- **Improvement**: +16.8% (+0.169)

### What These Metrics Mean

**Precision (0.899)**:
- Out of 100 names extracted, 90 are correct
- 10 are false positives (wrongly extracted)
- **High precision** = Few mistakes

**Recall (0.937)**:
- Out of 100 actual database names, 94 are caught
- 6 are missed (false negatives)
- **High recall** = Few misses

**F1 Score (0.918)**:
- Harmonic mean of precision and recall
- **0.918 is excellent** (scale: 0-1)
- Balanced performance on both metrics

### Performance Breakdown

**True Positives (TP)**: Names correctly extracted
- Example: Extracted "GenBank", paper actually mentions GenBank ✅

**False Positives (FP)**: Names wrongly extracted
- Example: Extracted "BLAST" but paper doesn't mention it ❌
- V1 FP count: Low (10% of extractions)

**False Negatives (FN)**: Names missed
- Example: Paper mentions "UniProt" but didn't extract it ❌
- V1 FN count: Low (6% of actual names)

---

## Evaluation Approach

### How NER is Evaluated

**From**: `analyze_llm_results.py` (lines 77-96)

```python
# Only evaluate on positive cases (papers that mention databases)
positive_cases = merged[merged['label_gt'] == True].copy()

# Parse ground truth and predicted databases
positive_cases['gt_dbs'] = positive_cases['ground_truth_databases'].apply(parse_databases)
positive_cases['pred_dbs'] = positive_cases['databases_pred'].apply(parse_databases)

# Calculate NER metrics
tp_ner = sum(len(row['gt_dbs'] & row['pred_dbs']) for _, row in positive_cases.iterrows())
fp_ner = sum(len(row['pred_dbs'] - row['gt_dbs']) for _, row in positive_cases.iterrows())
fn_ner = sum(len(row['gt_dbs'] - row['pred_dbs']) for _, row in positive_cases.iterrows())

# Calculate precision, recall, F1
precision_ner = tp_ner / (tp_ner + fp_ner) if (tp_ner + fp_ner) > 0 else 0
recall_ner = tp_ner / (tp_ner + fn_ner) if (tp_ner + fn_ner) > 0 else 0
f1_ner = 2 * precision_ner * recall_ner / (precision_ner + recall_ner)
```

### Evaluation Steps

**1. Filter to Positive Cases**
- Only papers that mention databases (label = positive)
- Negative papers have no databases to extract

**2. Parse Database Names**
```python
def parse_databases(db_str: str) -> Set[str]:
    """Parse JSON array of database names."""
    databases = json.loads(db_str)  # Parse JSON
    return {normalize_database_name(db) for db in databases}

def normalize_database_name(name: str) -> str:
    """Normalize for comparison."""
    return name.lower().strip().replace("database", "").replace("db", "").strip()
```

**3. Compare Sets**
- Ground truth: `gt_dbs` (correct database names)
- Predicted: `pred_dbs` (extracted names)
- Intersection: `gt_dbs & pred_dbs` (correct extractions)
- Difference: `pred_dbs - gt_dbs` (false positives)
- Difference: `gt_dbs - pred_dbs` (missed names)

**4. Calculate Metrics**
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = 2 × (Precision × Recall) / (Precision + Recall)

### Name Normalization for Evaluation

**Purpose**: Allow flexible matching (case-insensitive, variant handling)

**Normalization Steps**:
1. Convert to lowercase: "GenBank" → "genbank"
2. Strip whitespace: " PDB " → "pdb"
3. Remove common suffixes: "UniProt Database" → "uniprot"

**Example Matches**:
```
"GenBank" == "genbank" == "GENBANK"  ✅ (same after normalization)
"PDB" == "Protein Data Bank"  ❌ (different names, both should be extracted)
"UniProt Database" == "UniProt"  ✅ (same after removing "database")
```

---

## Best Practices Summary

### Do's ✅

1. **Extract both acronyms and full names** when provided
2. **Check both title and abstract** for database mentions
3. **Use context clues** (deposited in, using, obtained from)
4. **Deduplicate** multiple mentions of same database
5. **Extract names as they appear** in text (preserve case during extraction)
6. **Assign appropriate confidence** based on context clarity
7. **Verify it's a biodata resource**, not coincidental name match

### Don'ts ❌

1. **Don't extract programming languages** (Python, R, Java)
2. **Don't extract lab methods** (PCR, ELISA, Western blot)
3. **Don't extract statistical methods** (PCA, regression, t-test)
4. **Don't extract generic terms** ("database" without specific name)
5. **Don't hallucinate names** not present in text
6. **Don't extract general software** (Excel, SPSS)
7. **Don't normalize during extraction** (normalize only for evaluation)

---

## Common Errors to Avoid

### Error 1: Extracting Generic Terms ❌

**Wrong**:
```
Input: "We performed database analysis..."
Output: ["database"]  ❌ (generic term, no specific database)
```

**Right**:
```
Input: "We performed database analysis..."
Output: []  ✅ (no specific database mentioned)
```

---

### Error 2: Missing Acronyms ❌

**Wrong**:
```
Input: "Gene Expression Omnibus (GEO)"
Output: ["Gene Expression Omnibus"]  ❌ (missed GEO)
```

**Right**:
```
Input: "Gene Expression Omnibus (GEO)"
Output: ["Gene Expression Omnibus", "GEO"]  ✅ (both extracted)
```

---

### Error 3: Extracting Software Tools ❌

**Wrong**:
```
Input: "Analysis performed using Python and R"
Output: ["Python", "R"]  ❌ (programming languages, not databases)
```

**Right**:
```
Input: "Analysis performed using Python and R"
Output: []  ✅ (no biodata resources)
```

---

### Error 4: Missing Title Mentions ❌

**Wrong**:
```
Title: "ArachnoServer: spider toxin database"
Abstract: "We present a comprehensive resource..."
Output: []  ❌ (missed ArachnoServer from title)
```

**Right**:
```
Title: "ArachnoServer: spider toxin database"
Abstract: "We present a comprehensive resource..."
Output: ["ArachnoServer"]  ✅ (extracted from title)
```

---

### Error 5: Duplicating Names ❌

**Wrong**:
```
Input: "GEO database...from GEO...deposited in GEO"
Output: ["GEO", "GEO", "GEO"]  ❌ (duplicates)
```

**Right**:
```
Input: "GEO database...from GEO...deposited in GEO"
Output: ["GEO"]  ✅ (deduplicated)
```

---

## Tools and Resources

### Evaluation Script

**File**: `analyze_llm_results.py`
**Usage**:
```bash
python analyze_llm_results.py
```

**Output**:
- Classification metrics (accuracy, precision, recall, F1)
- NER metrics (precision, recall, F1)
- Comparison to BERT baseline
- Confusion matrices

### Test Data

**Location**: `data/llm_comparison/`

**Files**:
- `test_set_combined_300.csv` - Test papers (100 positive, 200 negative)
- `training_set_combined_100.csv` - Few-shot examples
- `results/claude_sonnet_predictions.csv` - Example output

### Documentation

**Location**: `data/llm_comparison/prompts/`

**Key Files**:
- `README.md` - Complete prompts guide
- `LLM_TESTING_INSTRUCTIONS.md` - Full testing instructions
- `detailed_prompt_design.md` - Prompt engineering details
- `v2_agent_batch_processing_improved.txt` - Latest prompt version

---

## Frequently Asked Questions

### Q1: What if a database is mentioned only in the title?

**A**: Extract it! Check both title AND abstract.

Example:
```
Title: "GenBank: comprehensive nucleotide database"
Abstract: "We describe updates to the resource..."
Output: ["GenBank"]  ✅
```

---

### Q2: Should I extract version numbers?

**A**: Optional. Include if emphasized in text.

```
"UniProt 2024.1" → ["UniProt"] or ["UniProt 2024.1"] (both acceptable)
"ArachnoServer 3.0" → ["ArachnoServer 3.0"] (version is part of name)
```

---

### Q3: What about database URLs?

**A**: Extract the database name, not the URL.

```
Input: "Available at http://www.genbank.org/"
Output: ["GenBank"]  ✅ (not the URL)
```

---

### Q4: How do I handle ambiguous acronyms?

**A**: Use context, assign lower confidence if uncertain.

```
"GO analysis" → Could be Gene Ontology or verb "go"
→ Check context, extract ["GO"] with "low" confidence if ambiguous
```

---

### Q5: What if I'm unsure if something is a database?

**A**: Be conservative. When in doubt, DON'T extract.

Better to miss a few (low recall) than extract many wrong names (low precision).

---

### Q6: Should I extract paper-specific database names?

**A**: Yes, if the paper introduces a new database.

```
Title: "MyNewDB: a novel cancer genomics resource"
Output: ["MyNewDB"]  ✅ (new database being introduced)
```

---

### Q7: What about Bioconductor packages?

**A**: Usually NO, unless specifically described as a database.

```
"DESeq2 R package" → NO (analysis package)
"AnnotationHub database" → YES (database resource)
```

---

## Summary

**NER Task**: Extract specific biodata resource names from abstracts

**Key Principles**:
1. Extract specific names (not generic terms)
2. Include both acronyms and full names
3. Check title AND abstract
4. Deduplicate multiple mentions
5. Exclude software, lab methods, statistical methods

**Performance**:
- V1 achieves 0.918 F1 (excellent)
- Beats BERT baseline by +16.8%
- 90% precision, 94% recall

**Output Format**:
```json
{
  "databases": ["GenBank", "PDB", "UniProt"],
  "confidence": "high"
}
```

**Evaluation**: Set-based matching with name normalization

---

**Last Updated**: 2025-10-31
**Version**: 1.0
**Related Documentation**:
- `data/llm_comparison/prompts/README.md` - Complete prompts guide
- `data/llm_comparison/results/ANALYSIS_SUMMARY.md` - Performance analysis
- `docs/COMPREHENSIVE_IMPLEMENTATION_PLAN.md` - Full project plan
