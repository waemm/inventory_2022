# CRITICAL FALSE POSITIVES - Manual Review Required

**Date**: 2025-11-27
**Analyst**: Code Review System

## Executive Summary

Out of 631 papers with URLs extracted, **29 cases (4.6%)** have REFERENCE URLs instead of the actual database being announced. These are critical failures that require manual correction.

## Why These Are Critical

The URL extraction script found URLs that are **well-known reference databases** (NCBI, UniProt, EBI, KEGG, etc.) rather than the novel database/resource being announced in the paper. This means:

1. **Wrong URL captured** - We have a reference citation, not the actual database
2. **Missing the real URL** - The actual database URL is elsewhere in the full text
3. **High scores on wrong URLs** - Some have high scores (up to 73), showing the scoring system can be fooled

## False Positive Patterns

### Pattern 1: NCBI/GenBank URLs (7 cases)
Papers announcing NEW databases but script captured NCBI references:
- **PMID 30834332** (RefSoil+) → captured NCBI RefSeq FTP
- **PMID 34698276** (MicroSalmon) → captured NCBI genome annotation
- **PMID 33767203** (NLM-Chem) → captured NCBI research data page (score: 73!)
- **PMID 32792559** (ACDC amphibian database) → captured GenBank (score: 55)
- **PMID 26255307** (Phytochemica) → captured PubMed
- **PMID 34762696** (Trypanosoma/Leishmania) → captured NCBI genome
- **PMID 32850476** (TickSialoFam) → captured NCBI BLAST FTP

### Pattern 2: EBI URLs (6 cases)
EBI hosts many databases, but these are WRONG:
- **PMID 21992002** (BioLexicon) → captured EBI service URL (score: 73!)
- **PMID 34181736** (CROssBAR) → captured EBI Tools/crossbar (score: 73!)
- **PMID 25281234** (CanvasDB) → captured 1000 Genomes EBI FTP
- **PMID 28158609** (Enzyme Portal) → captured EBI enzyme portal (score: 63)
- **PMID 24316577** (NHGRI GWAS Catalog) → captured EBI GWAS (score: 55)
- **PMID 32255760** (AMR surveillance) → captured EBI ENA pathogens
- **PMID 32859947** (Endometrium database) → captured EBI genenames FTP (score: 63)

### Pattern 3: CRAN/Bioconductor (4 cases)
R package repositories instead of the actual tool:
- **PMID 28981643** (MareyMap) → CRAN package page (score: 65)
- **PMID 28096900** (MS_HistoneDB) → CRAN pheatmap package
- **PMID 29989589** (FRY fire database) → CRAN SDMTools
- **PMID 30416602** (Sturany specimens) → CRAN oceanmap
- **PMID 32954379** (MS Atlas) → Bioconductor org.Hs.eg.db

### Pattern 4: Other Common References (12 cases)
- **KEGG**: PMID 29470400 (RaMP) → KEGG REST API (score: 50)
- **UniProt**: PMID 22737123 (SynProt) → uniprot.org
- **ExPASy**: PMID 30053271 (PharmacoDB) → ExPASy Cellosaurus
- **OMIM**: PMID 33258967 (ncVarDB) → omim.org
- **STRING**: PMID 26982336 (PUFs) → string-db.org
- **HapMap**: PMID 21659040 (EPR) → HapMap NCBI
- **Apache.org**: PMID 21466708, 21930505, 26373861 → Apache software URLs

## Highest Priority Cases (Score ≥ 50)

These had HIGH CONFIDENCE but are WRONG:

| PMID | Score | Title | Wrong URL | Domain |
|------|-------|-------|-----------|--------|
| 21992002 | 73 | BioLexicon | ebi.ac.uk/Rebholz-srv/BioLexicon | EBI |
| 34181736 | 73 | CROssBAR | ebi.ac.uk/Tools/crossbar | EBI |
| 33767203 | 73 | NLM-Chem | ncbi.nlm.nih.gov/research/bionlp | NCBI |
| 28981643 | 65 | MareyMap | cran.r-project.org/...MareyMap | CRAN |
| 28158609 | 63 | Enzyme Portal | ebi.ac.uk/enzymeportal | EBI |
| 32859947 | 63 | Endometrium DB | ftp.ebi.ac.uk/.../genenames | EBI |
| 32792559 | 55 | ACDC (amphibian) | ncbi.nlm.nih.gov/genbank | NCBI |
| 24316577 | 55 | NHGRI GWAS Catalog | ebi.ac.uk/fgpt/gwas | EBI |
| 29470400 | 50 | RaMP | rest.kegg.jp/list/pathway | KEGG |

**These 9 cases are particularly problematic** because the scoring system gave them high confidence despite being completely wrong.

## Recommended Actions

### Immediate (Manual Review)
1. **Review all 29 cases** - Find the correct database URLs from the full text
2. **Update the extraction results** - Replace wrong URLs with correct ones
3. **Document patterns** - Note where the correct URLs were found (abstract, methods, data availability, etc.)

### Short-term (Script Improvement)
1. **Blacklist reference domains** - Filter out NCBI, EBI, UniProt, KEGG, CRAN, etc. BEFORE scoring
2. **Penalize well-known domains** - If these do appear, give them very low scores
3. **Context analysis** - Look for phrases like "available at", "accessible at" near URLs
4. **Prefer unique domains** - URLs with unique domains (not .gov, not major databases) should score higher

### Long-term (Validation)
1. **Compare with abstracts** - The URL in abstract is often more reliable
2. **Cross-check with known databases** - Use existing bioresource registries
3. **Human validation** - Sample 10% of high-score URLs for quality control

## Files Generated

1. **review_extraction_issues.csv** - All 383 flagged issues
2. **review_extraction_summary.md** - Detailed analysis with examples
3. **CRITICAL_FALSE_POSITIVES.md** (this file) - Focus on the 29 critical cases

## Next Steps

1. Manual review of the 29 false positive cases
2. Update scoring algorithm to avoid reference URLs
3. Re-run extraction on these 29 papers with improved logic
4. Validate the corrections
