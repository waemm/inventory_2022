# False Positive Detection Guide for Bioresource Classification

## Overview

This document provides guidance for reviewing papers that have been classified as potential bioresources. Your task is to determine whether each paper is a **TRUE BIORESOURCE** or a **FALSE POSITIVE** based primarily on the paper's **TITLE**.

## What is a Bioresource?

A **bioresource** is a publicly accessible data repository, database, or data collection that:
- Houses curated biological, genomic, proteomic, or biomedical data
- Is accessible via a URL/web interface
- Provides data that other researchers can query, download, or analyze
- Is the PRIMARY subject of the paper (the paper announces/describes/updates the resource)

## What is NOT a Bioresource (False Positives)?

**False positives** are papers that appear in our results but do NOT describe a bioresource. Common types include:

### 1. Pure Methodology/Tool Papers
Papers describing computational tools, algorithms, pipelines, or methods WITHOUT an associated data repository.

**FALSE POSITIVE Examples:**
- "A computational tool for predicting protein structure"
- "DeepPredict: A deep learning approach for variant classification"
- "A pipeline for analyzing single-cell RNA-seq data"
- "Novel algorithm for detecting somatic mutations"
- "inTB - a data integration platform" - Integration platforms are tools, NOT databases

**Key Title Patterns (FALSE POSITIVE indicators):**
- "tool for [doing something]"
- "method for [doing something]"
- "approach for [doing something]"
- "algorithm for [doing something]"
- "pipeline for [analyzing/processing]"
- "framework for [prediction/analysis]"
- "predicting [something]"
- "prediction of [something]"
- "detection of [something]"
- "identification of [something]"
- "integration platform" - these are tools for combining data, NOT databases

### 2. Analysis/Study Papers
Papers that USE existing databases to conduct research, rather than introducing a new resource.

**FALSE POSITIVE Examples:**
- "Genome-wide association study of diabetes using UK Biobank data"
- "Analysis of protein interactions in cancer cells"
- "Comprehensive analysis of mutation patterns in lung adenocarcinoma"
- "Machine learning classification of tumor subtypes"

### 3. Review/Commentary Papers
Papers that review a field or discuss methodological approaches.

**FALSE POSITIVE Examples:**
- "A review of machine learning in genomics"
- "Current approaches in variant interpretation"
- "Best practices for RNA-seq analysis"

### 4. Software-Only Papers
Papers describing software tools that process data but don't house data.

**FALSE POSITIVE Examples:**
- "R package for statistical analysis of proteomics data"
- "Python library for sequence alignment"
- "Web server for protein structure prediction"
- "Integration platform for molecular data" - Platform for integration is a TOOL

---

## What IS a Bioresource (True Positives)?

**True positives** are papers that introduce, describe, or update a bioresource.

### Key Title Patterns (TRUE BIORESOURCE indicators):

**Strong indicators - Database Keywords:**
- "database" in title (e.g., "The Protein Database: a comprehensive resource")
- "knowledgebase" or "knowledge base" in title
- "repository" in title
- "archive" in title
- "atlas" in title

**Strong indicators - Name Suffixes (IMPORTANT!):**
These naming patterns almost always indicate a database:
- **[Name]DB** pattern: VIPERdb, FungiDB, MelanomaDB, TrypsNetDB, PhenoDB
- **[Name]Base** pattern: BorreliaBase, MINTbase (note: different from "knowledge base")
- **[Name]KB** pattern: OncoKB, PsyMuKB, UniCarbKB
- **[Name]pedia** pattern: CAZypedia, ASpedia, PmiREN (encyclopedias)
- **[Name]Map** pattern: lncRNAMap, pseudoMap (when describing data maps)
- **[Name]Hub** pattern: AcrHub (when it stores data)

**Strong indicators - Knowledge/Reference Terms:**
- "knowledge base" (as two words, describing stored knowledge)
- "encyclopedia" - collections of curated information
- "reference panel" - curated reference datasets
- "reference database" - reference collections
- "compendium" - comprehensive collections

**Moderate indicators:**
- "resource for [storing/accessing data]"
- "data portal"
- "data commons"
- "[year] update" or version numbers (e.g., "2.0", "v4.0") - often database updates
- "platform for exploring/mining [data]" - when the platform HOUSES data

**TRUE BIORESOURCE Examples:**
- "The Mouse Genome Database (MGD): comprehensive resource for genetics" → database keyword
- "UniProt Knowledgebase: a hub of integrated protein data" → knowledgebase keyword
- "DrugBank 4.0: shedding new light on drug metabolism" → Bank suffix + version
- "OncoKB: A Precision Oncology Knowledge Base" → KB suffix + knowledge base
- "CAZypedia: a living encyclopedia of carbohydrate-active enzymes" → pedia suffix + encyclopedia
- "VIPERdb: A Tool for Virus Research" → DB suffix overrides "tool" keyword
- "lncRNAMap: a map of putative regulatory functions" → Map suffix
- "jMorp: Japanese Multi Omics Reference Panel" → reference panel
- "POSTAR: a platform for exploring post-transcriptional regulation" → platform for exploring DATA

---

## Decision Framework

For each paper, evaluate the TITLE using this framework:

### Step 1: Check for Database Name Suffixes (HIGHEST PRIORITY)
Does the resource name end in: DB, Base, KB, pedia, Map, Hub?
- **YES** → Almost certainly TRUE BIORESOURCE (these override methodology patterns)
- **NO** → Continue to Step 2

### Step 2: Check for Database/Resource Words
Does the title contain: database, knowledgebase, knowledge base, repository, archive, atlas, encyclopedia, reference panel, compendium?
- **YES** → Likely TRUE BIORESOURCE (but verify it's about the resource itself)
- **NO** → Continue to Step 3

### Step 3: Check for Methodology Patterns
Does the title contain: "tool for", "method for", "approach for", "algorithm for", "pipeline for", "framework for", "predicting", "prediction of", "detection of", "integration platform"?
- **YES** → Likely FALSE POSITIVE (unless name has DB/KB/etc. suffix)
- **NO** → Continue to Step 4

### Step 4: Check URL Presence
Does the paper have a resource_url?
- **NO URL** → Strong indicator of FALSE POSITIVE
- **HAS URL** → May still be false positive if title is methodology-focused

### Step 5: Evaluate Overall Title Meaning
Ask: "Is this paper primarily ABOUT a data resource, or is it ABOUT a method/tool/analysis?"
- About a DATA RESOURCE → TRUE BIORESOURCE
- About a METHOD/TOOL/ANALYSIS → FALSE POSITIVE

---

## Edge Cases and Examples

### Edge Case 1: Name Suffix Overrides Methodology Words
When a resource name has a database suffix (DB, KB, Base, etc.), it IS a bioresource even if "tool" appears in title.

**TRUE BIORESOURCE (suffix overrides "tool"):**
- "VIPERdb: A Tool for Virus Research" → DB suffix = database
- "MelanomaDB: A Web Tool for Integrative Analysis" → DB suffix = database
- "PhenoDB: a new web-based tool for collection, storage, and analysis" → DB suffix = database

### Edge Case 2: Platform Distinction
"Platform" can be either a bioresource OR a tool depending on context:

**TRUE BIORESOURCE (platform that HOUSES data):**
- "SFGD: a comprehensive platform for mining functional information" → houses soybean data
- "POSTAR: a platform for exploring post-transcriptional regulation" → houses RNA data
- "TANRIC: An Interactive Open Platform to Explore lncRNAs in Cancer" → houses lncRNA data

**FALSE POSITIVE (platform that is a TOOL):**
- "inTB - a data integration platform" → integrates data from OTHER sources
- "An integration platform for molecular analysis" → tool for combining data
- "A computational platform for analysis" → analysis tool only

### Edge Case 3: Papers ABOUT Using a Database (Not the Database Itself)
Papers that describe using or applying a database are FALSE POSITIVES.

**FALSE POSITIVE:**
- "Using ConSurf to Detect Functionally Important Regions" → about USING a tool
- "Building networks Using MatrixDB" → about USING MatrixDB
- "Application of the DruGeVar Database in Cancer" → about APPLICATION of database

### Edge Case 4: Version Numbers Indicate Database Updates
Papers with version numbers often describe database updates - these ARE bioresources.

**TRUE BIORESOURCE:**
- "PlantPAN 2.0: an update of plant promoter analysis navigator"
- "eggNOG v4.0: nested orthology inference across 3686 organisms"
- "MiDAS 3: An ecosystem-specific reference database"

---

## Output Format

For each paper, provide:
1. **pmid**: The paper's PubMed ID
2. **title**: The paper's title
3. **has_url**: Whether it has a resource URL (True/False)
4. **is_false_positive**: Your classification (Y = False Positive, N = True Bioresource)
5. **confidence**: Your confidence level (high/medium/low)
6. **reason**: Brief explanation (1-2 sentences)
7. **database_name**: Short name/acronym of the database (if bioresource)
8. **long_database_name**: Full expanded name of the database (if bioresource)

### Database Name Extraction Rules

**For TRUE BIORESOURCES (is_false_positive = N), extract both names:**

- **database_name**: The short name, acronym, or branded name
  - Usually appears in parentheses: "The Mouse Genome Database **(MGD)**" → MGD
  - Or is the first word before a colon: "**VIPERdb**: A Tool for..." → VIPERdb
  - Or ends with DB/KB/Base suffix: "**OncoKB**: A Precision..." → OncoKB

- **long_database_name**: The full descriptive name
  - Usually appears before parentheses: "**The Mouse Genome Database** (MGD)" → The Mouse Genome Database
  - Or is the expanded form of the acronym: "**Virus Particle Explorer Database**" for VIPERdb
  - Or the descriptive phrase: "**Precision Oncology Knowledge Base**" for OncoKB

**If only one name exists**, use it in both fields.

**For FALSE POSITIVES (is_false_positive = Y)**, leave both name fields empty.

### Example Output:

| pmid | title | has_url | is_false_positive | confidence | reason | database_name | long_database_name |
|------|-------|---------|-------------------|------------|--------|---------------|-------------------|
| 31443733 | Variant Interpretation for Cancer (VIC): a computational tool | True | Y | high | Methodology tool, not a data resource | | |
| 24163257 | The mouse Gene Expression Database (GXD): 2014 update | True | N | high | Title explicitly names a database | GXD | Mouse Gene Expression Database |
| 34876593 | A computational approach for discovery of cancer genes | False | Y | high | Pure methodology paper | | |
| 25925569 | piRBase: a web resource assisting piRNA functional study | True | N | high | Base suffix indicating database | piRBase | piRNA Database |
| 28890946 | OncoKB: A Precision Oncology Knowledge Base | True | N | high | KB suffix + Knowledge Base | OncoKB | Precision Oncology Knowledge Base |
| 23875173 | MelanomaDB: A Web Tool for Integrative Analysis | True | N | high | DB suffix overrides "tool" | MelanomaDB | Melanoma Genomic Database |
| 24001185 | inTB - a data integration platform | True | Y | high | Integration platform is a tool | | |
| 29040563 | Ten years of CAZypedia: a living encyclopedia | True | N | high | pedia suffix + encyclopedia | CAZypedia | Carbohydrate-Active Enzymes Encyclopedia |
| 30841849 | mGAP: the macaque genotype and phenotype resource | True | N | high | Contains "resource" | mGAP | Macaque Genotype and Phenotype Resource |

---

## Standardized Reason Templates

**IMPORTANT:** Use these standardized reason templates to ensure consistent classification language across all reviews. This enables automated analysis and clear understanding of why each paper was classified.

### For FALSE POSITIVES (is_false_positive = Y)

#### Category 1: Bioresource mentioned but no URL (NEEDS MANUAL URL RESEARCH)
Use when title clearly describes a database/resource but paper lacks URL:
```
Database mentioned but no URL, not accessible
Atlas mentioned but no URL, not accessible
Knowledge base mentioned but no URL, not accessible
Repository mentioned but no URL, not accessible
Resource mentioned but no URL, not accessible
Catalogue mentioned but no URL, not accessible
Assay resource mentioned but no URL, not accessible
Database and atlas mentioned but no URL, not accessible
```

#### Category 2: Paper ABOUT database work (not the database itself)
Use when paper describes database-related work but isn't announcing the database:
```
Paper about database construction, not the database
Paper about creating database, not the database itself
Paper about improving [X], not a new database
Paper about database need/framework, no URL confirms not operational
Database development paper, no URL
```

#### Category 3: Tool/Method using database technology
Use when paper describes a tool that uses or queries databases:
```
Tool implementation using database technology, not a bioresource
Integration tool using existing database, not a new database
Tool for database management, not a bioresource
Algorithm for querying existing data, not a database
Indexing method for databases, not a database
Database for tool evaluation, not a bioresource
```

#### Category 4: Pure methodology/tool papers
Use when paper clearly describes a method or tool:
```
[Specific] tool, not a database
[Specific] method, not a database
[Specific] algorithm, not a database
[Specific] platform/tool, not a database
Protocol/methodology paper, not a database
Analysis and methodology resource, not a data repository
```

**Examples with specifics:**
```
Prediction tool, not a database
Annotation tool, not a database
Visualization tool, not a database
Screening platform/method, not a database
Phenotyping platform/tool, not a database
Tool for k-mer statistics, not a database
Method for atlas warping, not a database
Method for drug repurposing, not a database
Correction method/tool, not a database
Method/tool for haplotype estimation, not a database
```

#### Category 5: Papers about using existing resources
Use when paper describes using/applying an existing database:
```
Paper about using [database name], not the database itself
Analysis using existing database, not a new resource
Tool for accessing existing resource, not a new database
```

### For TRUE BIORESOURCES (is_false_positive = N)

Use clear, specific reasons:
```
DB suffix + 'database' keyword
KB suffix + knowledge base keyword
Base suffix indicating database
pedia suffix + encyclopedia keyword
Database keyword in title
Atlas keyword indicates data resource
Repository keyword in title
Version number indicates database update
Explicit database with curated data
Reference panel/database keyword
```

### Reason Template Structure

Follow this pattern for clarity:
```
[What is identified] + [why it's classified this way]
```

**Good examples:**
- "Database mentioned but no URL, not accessible"
- "Tool for prediction, not a database"
- "DB suffix overrides tool keyword"
- "Paper about using database, not the database itself"

**Avoid vague reasons like:**
- "No URL" (too brief - specify what's missing URL)
- "Methodology" (too vague - specify what kind)
- "Tool" (specify what the tool does)

---

## Summary Checklist

Before classifying each paper, verify:

1. [ ] Does the name have a database suffix (DB, Base, KB, pedia, Map, Hub)? → **TRUE BIORESOURCE** (overrides methodology patterns)
2. [ ] Does the title contain "database", "knowledgebase", "encyclopedia", "reference panel"? → Lean TRUE BIORESOURCE
3. [ ] Does the title contain "tool for", "method for", "integration platform"? → Lean FALSE POSITIVE (unless name suffix exists)
4. [ ] Does the paper have a resource URL? → No URL = Strong FALSE POSITIVE indicator
5. [ ] Is the paper's primary purpose to describe a DATA COLLECTION or a METHOD?

**Priority Rule:** Name suffixes (DB, KB, Base, pedia, Map) take priority over methodology keywords.

**When in doubt:** If the title emphasizes methodology/computation over data curation AND has no database suffix, classify as FALSE POSITIVE.
