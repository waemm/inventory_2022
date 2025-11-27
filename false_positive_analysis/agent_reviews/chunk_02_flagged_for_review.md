# Chunk 02: Cases Flagged for Manual Review

## Overview
Out of 500 papers reviewed, the following cases are flagged for manual verification due to low/medium confidence or unusual patterns.

## Category 1: True Bioresources WITHOUT URL (9 cases)
**Risk**: These claim to be databases but lack URLs - may be false positives

| PMID | Title | Confidence | Reason |
|------|-------|------------|--------|
| 30408350 | Investigation of RNA-RNA Interactions Using the RISE Database. | High | Contains database/repository keyword |
| 24958384 | The gene expression database for mouse development (GXD): putting developmental expression information at your fingertips. | - | Contains database keyword but no URL |
| 21272355 | Animal model integration to AutDB, a genetic database for autism. | - | Contains database keyword but no URL |
| 29761470 | Navigating the i5k Workspace@NAL: A Resource for Arthropod Genomes. | - | Contains resource keyword but no URL |
| 31813695 | Using research to guide practice: The Physiotherapy Evidence Database (PEDro). | - | Contains database keyword but no URL |

**Action Needed**: Verify if these are actually describing databases or just papers that USE databases

---

## Category 2: Low-Confidence False Positives (27 cases)
**Risk**: May actually be databases that were misclassified

Selected examples that need review:

| PMID | Title | Has URL | Reason for Low Confidence |
|------|-------|---------|---------------------------|
| 24525374 | lncRNAMap: a map of putative regulatory functions in the long non-coding transcriptome. | True | Unclear from title - could be database or tool |
| 27242503 | Building the Ferretome. | True | Ambiguous title without clear database indicators |
| 22427539 | The SMART Platform: early experience enabling substitutable applications for electronic health records. | True | Platform paper - unclear if data resource |
| 31797632 | PGxMine: Text mining for curation of PharmGKB. | True | Mining tool - likely NOT a database |
| 33471060 | Cellinker: a platform of ligand-receptor interactions for intercellular communication analysis. | True | Platform for analysis - may house data |
| 23110173 | SEED servers: high-performance access to the SEED genomes, annotations, and metabolic models. | True | Servers for access - likely IS a database |

---

## Category 3: Medium-Confidence False Positives (25 cases)
**Risk**: Papers with database keywords but also methodology patterns

Selected examples:

| PMID | Title | Has URL | Classification Reason |
|------|-------|---------|----------------------|
| 33045741 | LncSEA: a platform for long non-coding RNA related sets and enrichment analysis. | True | Platform for ANALYSIS not data storage |
| 24712981 | SFGD: a comprehensive platform for mining functional information from soybean transcriptome data... | True | Platform for MINING - tool emphasis |
| 28850115 | RefEx, a reference gene expression dataset as a web tool for the functional analysis of genes. | True | Web TOOL for analysis |
| 28724888 | CrossCheck: an open-source web tool for high-throughput screen data analysis. | True | Web TOOL for analysis |
| 28053162 | POSTAR: a platform for exploring post-transcriptional regulation coordinated by RNA-binding proteins. | True | Platform for EXPLORING - analysis tool |
| 27797767 | miRNAmeConverter: an R/bioconductor package for translating mature miRNA names... | True | R PACKAGE - software tool |
| 23071556 | MK4MDD: a multi-level knowledge base and analysis platform for major depressive disorder. | True | PLATFORM for analysis |

---

## Category 4: Low-Confidence True Bioresources (18 cases)
**Risk**: May be methodology papers misclassified as databases

Selected examples that need verification:

| PMID | Title | Has URL | Why Low Confidence |
|------|-------|---------|-------------------|
| 26708988 | HitPredict version 4: comprehensive reliability scoring of physical protein-protein interactions... | True | Focus on "scoring" - may be tool |
| 24178034 | IDEAL in 2014 illustrates interaction networks... | True | "Illustrates" networks - unclear if database |
| 23203986 | Genome3D: a UK collaborative project to annotate genomic sequences... | True | Project focus rather than database focus |
| 22363733 | PrionHome: a database of prions and other sequences... | True | Should be high confidence - review |
| 24170407 | PRALINE: a versatile multiple sequence alignment toolkit. | True | TOOLKIT - likely FALSE POSITIVE |

---

## Recommendations

### Immediate Actions:
1. **Review 9 "databases" without URLs** - These are suspicious and likely false positives
2. **Spot-check 10 low-confidence false positives** - Verify tool vs. database distinction
3. **Validate medium-confidence cases** - Especially "platforms" that may house data

### Specific Cases to Review:
- **PRALINE (24170407)**: Called "toolkit" but classified as database - likely ERROR
- **SEED servers (23110173)**: Likely IS a database despite low confidence
- **Building the Ferretome (27242503)**: Ambiguous title needs abstract review

### Pattern Observations:
- "Platform for [analysis/mining]" → Usually tools, not databases
- "Web tool for" → Usually NOT databases
- "R/Bioconductor package" → Usually software, not databases
- Papers without URLs claiming to be databases → Highly suspicious

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| **Total flagged for review** | 79 (15.8%) |
| **High priority (no URL databases)** | 9 (1.8%) |
| **Medium priority (low conf FP)** | 27 (5.4%) |
| **Low priority (other)** | 43 (8.6%) |

---

## Next Steps

1. Conduct manual abstract review for high-priority cases
2. Validate 10-20 random samples from each confidence category
3. Refine classification rules based on manual review findings
4. Document any systematic misclassification patterns
