# URL Extraction Results Review
**Analysis Date**: 2025-11-27
**Input File**: novel_fulltext_url_results.csv

## Overall Statistics
- **Total records analyzed**: 1108
- **Records with URLs found**: 631
- **Total issues flagged**: 383
- **Issue rate**: 60.7% of records with URLs

## Issues by Type

- **DEAD_HIGH_SCORE**: 202 cases
- **LOW_SCORE**: 152 cases
- **FALSE_POSITIVE_URL**: 29 cases

## Examples by Issue Type

### Dead High Score

**PMID 32542364**
- Title: GTDB: an integrated resource for glycosyltransferase sequences and annotations....
- URL: https://www.biosino.org/gtdb/
- Score: 73.0
- Title Match: True
- Issue: Dead URL with high score (73.0) - may need investigation

**PMID 31032842**
- Title: The MACADAM database: a MetAboliC pAthways DAtabase for Microbial taxonomic groups for mining potent...
- URL: http://macadam.toulouse.inra.fr
- Score: 50.0
- Title Match: True
- Issue: Dead URL with high score (50.0) - may need investigation

**PMID 22139914**
- Title: MOPED: Model Organism Protein Expression Database....
- URL: http://moped.proteinspire.org
- Score: 63.0
- Title Match: True
- Issue: Dead URL with high score (63.0) - may need investigation

**PMID 26504853**
- Title: FluKB: A Knowledge-Based System for Influenza Vaccine Target Discovery and Analysis of the Immunolog...
- URL: http://research4.dfci.harvard.edu/cvc/flukb/
- Score: 65.0
- Title Match: True
- Issue: Dead URL with high score (65.0) - may need investigation

**PMID 26882984**
- Title: RhesusBase PopGateway: Genome-Wide Population Genetics Atlas in Rhesus Macaque....
- URL: http://www.rhesusbase.org/popGateway
- Score: 55.0
- Title Match: True
- Issue: Dead URL with high score (55.0) - may need investigation

### False Positive Url

**PMID 30834332**
- Title: RefSoil+: a Reference Database for Genes and Traits of Soil Plasmids....
- URL: ftp://ftp.ncbi.nlm.nih.gov/refseq/release
- Score: 13.0
- Title Match: False
- Issue: Reference URL detected () - likely not the announced database

**PMID 29470400**
- Title: RaMP: A Comprehensive Relational Database of Metabolomics Pathways for Pathway Enrichment Analysis o...
- URL: http://rest.kegg.jp/list/pathway/hsa
- Score: 50.0
- Title Match: True
- Issue: Reference URL detected (rest.kegg.jp) - likely not the announced database

**PMID 21992002**
- Title: The BioLexicon: a large-scale terminological resource for biomedical text mining....
- URL: http://www.ebi.ac.uk/Rebholz-srv/BioLexicon/biolexicon.html
- Score: 73.0
- Title Match: True
- Issue: Reference URL detected (www.ebi.ac.uk) - likely not the announced database

**PMID 28981643**
- Title: MareyMap Online: A User-Friendly Web Application and Database Service for Estimating Recombination R...
- URL: https://cran.r-project.org/web/packages/MareyMap/index.html
- Score: 65.0
- Title Match: True
- Issue: Reference URL detected (cran.r-project.org) - likely not the announced database

**PMID 25281234**
- Title: CanvasDB: a local database infrastructure for analysis of targeted- and whole genome re-sequencing p...
- URL: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/release/20110521/
- Score: 13.0
- Title Match: False
- Issue: Reference URL detected () - likely not the announced database

### Low Score

**PMID 35088001**
- Title: The GWAS-MAP platform for aggregation of results of genome-wide association studies and the GWAS-MAP...
- URL: http://www.ukbiobank.ac.uk/
- Score: 13.0
- Title Match: False
- Issue: Low score (13.0) - URL may be incorrect

**PMID 34669691**
- Title: RefPlantNLR is a comprehensive collection of experimentally validated plant disease resistance prote...
- URL: https://www.geneious.com
- Score: 8.0
- Title Match: False
- Issue: Low score (8.0) - URL may be incorrect

**PMID 31286860**
- Title: DAIRYdb: a manually curated reference database for improved taxonomy annotation of 16S rRNA gene seq...
- URL: http://www.drive5.com/uchime/rdp_gold.fa
- Score: 10.0
- Title Match: False
- Issue: Low score (10.0) - URL may be incorrect

**PMID 31598718**
- Title: SEAweb: the small RNA Expression Atlas web application....
- URL: http://sea.ims.bio/
- Score: 18.0
- Title Match: False
- Issue: Low score (18.0) - URL may be incorrect

**PMID 30339215**
- Title: MGH: a genome hub for the medicinal plant maca (Lepidium meyenii)....
- URL: http://ccdb.tau.ac.il/search/
- Score: 11.0
- Title Match: False
- Issue: Low score (11.0) - URL may be incorrect

## Recommendations

### 1. False Positive URLs (29 cases)
**Critical Issue**: These papers have reference URLs (NCBI, UniProt, etc.) instead of their announced database URLs.

**Action Required**:
- Manual review of each case to find correct URL
- Update scoring logic to penalize common reference domains
- Consider filtering out known reference URLs before scoring

### 3. Low Score URLs (152 cases)
**Issue**: URLs found with low confidence scores (<20).

**Action Required**:
- Manual review to verify correctness
- Consider increasing minimum score threshold
- May indicate weak signals that need human verification

### 4. Dead URLs with High Scores (202 cases)
**Issue**: High-confidence URLs that are no longer accessible.

**Action Required**:
- Check Internet Archive for archived versions
- Look for updated URLs in recent citations
- May be temporary outages - recheck later

## Priority for Manual Review

1. **FALSE_POSITIVE_URL** - Highest priority, these are likely wrong
2. **SUSPICIOUS_TITLE_MATCH** - Medium priority, may be correct but need verification
3. **LOW_SCORE** - Medium priority, uncertain matches
4. **DEAD_HIGH_SCORE** - Lower priority, likely correct but need URL updates

