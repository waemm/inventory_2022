# IUPHAR-DB/GtoPdb Pipeline Investigation Report

**Date**: 2025-12-10
**Purpose**: Investigate why IUPHAR-DB/Guide to PHARMACOLOGY papers are underrepresented in the biodata inventory pipeline

---

## Executive Summary

This investigation traced the IUPHAR-DB/GtoPdb resource through the entire pipeline to understand coverage gaps. Key findings:

| Stage | Papers Found | Notes |
|-------|--------------|-------|
| Key IUPHAR Papers (known) | 7 | Most-cited database update papers |
| In Original 2022 Query | 12 | Includes some related papers |
| In Original 2022 Inventory | 2 | Only 2012 papers made it through |
| In Updated Pipeline (2025) | 5 of 7 | Significant improvement |
| Missing Due to Query Gap | 2 | MeSH term "Databases, Pharmaceutical" not in query |

**Root Causes Identified**:
1. Missing MeSH term in query excludes most-cited papers
2. V2 NER failed to extract entities from key rebranding paper (2014)
3. No alias linking between "IUPHAR-DB" and "Guide to PHARMACOLOGY"

---

## 1. The IUPHAR-DB Resource

### Background
- **Original name**: IUPHAR-DB (International Union of Basic and Clinical Pharmacology Database)
- **Rebranded to**: Guide to PHARMACOLOGY (GtoPdb) in 2014
- **Most cited paper**: PMID 29149325 (2018) - 2,391 citations

### Key Papers (7 database update papers)

| PMID | Year | Title | Citations |
|------|------|-------|-----------|
| 22674159 | 2012 | IUPHAR-DB: new receptors and tools | 38 |
| 23087376 | 2012 | IUPHAR-DB: updated database content | 77 |
| 24234439 | 2014 | The IUPHAR/BPS Guide to PHARMACOLOGY (rebranding) | 688 |
| 26464438 | 2016 | The IUPHAR/BPS Guide to PHARMACOLOGY 2016 | 548 |
| 29149325 | 2018 | The IUPHAR/BPS Guide to PHARMACOLOGY 2018 | 2,391 |
| 31691834 | 2020 | The IUPHAR/BPS Guide to PHARMACOLOGY 2020 | 1,066 |
| 34718737 | 2022 | The IUPHAR/BPS Guide to PHARMACOLOGY 2022 | 588 |

---

## 2. Original 2022 Query Analysis

### Papers in Original Query (epmc_query_results_2022.csv)

From the original 21,678 papers, **12 mention IUPHAR or GtoPdb**:

| PMID | Year | In Query | In Final Inventory |
|------|------|----------|-------------------|
| 22674159 | 2012 | ✅ | ✅ |
| 23087376 | 2012 | ✅ | ✅ |
| 24234439 | 2014 | ✅ | ❌ |
| 26464438 | 2016 | ✅ | ❌ |
| 29149325 | 2018 | ❌ | ❌ |
| 31691834 | 2020 | ✅ | ❌ |
| 34718737 | 2022 | ❌ | ❌ |

**Additional IUPHAR-related papers in query** (5 more):
- PMIDs: 21149260, 23193265, 24271396, 27085512, 35218845

### Why Papers Are Missing from Query

**PMID 29149325** (most cited, 2,391 citations) has only one MeSH term:
- `Databases, Pharmaceutical`

This MeSH term is **NOT in the query**. The current query includes:
- `Databases, Genetic`
- `Databases, Protein`
- `Databases, Factual`
- `Databases, Nucleic Acid`
- `Knowledge Bases`

**Recommendation**: Add `MESH:"Databases, Pharmaceutical"` to query.

---

## 3. Classification Stage Analysis

### 2025 Rerun Results (collab_results/2025-10-24-s4985d_2022_rerun)

All IUPHAR papers in the query **passed classification** as bio-resources:

| PMID | Classification | Confidence |
|------|---------------|------------|
| 22674159 | bio-resource | ✅ |
| 23087376 | bio-resource | ✅ |
| 24234439 | bio-resource | ✅ |
| 26464438 | bio-resource | ✅ |
| 31691834 | bio-resource | ✅ |

**Finding**: Classification is NOT the bottleneck.

---

## 4. NER Stage Analysis

### V2 BERT NER Results (2025-10-24 rerun)

| PMID | Entities Extracted | Issue |
|------|-------------------|-------|
| 22674159 | "IUPHAR-DB" | ✅ Works |
| 23087376 | "IUPHAR-DB" | ✅ Works |
| 24234439 | **NONE** | ❌ Critical failure |
| 26464438 | "G", "IUPHAR/BPS Guide to PHARMACOLOGY" | ⚠️ Partial (has noise) |
| 31691834 | "GtoPdb", "Guide to PHARMACOLOGY" | ✅ Works |

### Critical Issue: PMID 24234439 (2014 Rebranding Paper)

This paper announces the rebranding from "IUPHAR-DB" to "Guide to PHARMACOLOGY". Despite being correctly classified as a bio-resource, V2 NER extracted **zero entities**.

**Abstract excerpt**:
> "The IUPHAR/BPS Guide to PHARMACOLOGY (http://www.guidetopharmacology.org) is a new open-access resource that unites the data from the IUPHAR-DB and the published BPS 'Guide to Receptors and Channels' (GRAC)..."

The abstract clearly contains extractable entities:
- "Guide to PHARMACOLOGY"
- "IUPHAR-DB"
- URL: http://www.guidetopharmacology.org

**Root Cause**: V2 NER model failed on this text pattern.

---

## 5. spaCy Hybrid NER Analysis

### Historical Issue (Fixed)

Earlier investigation revealed that the spaCy statistical NER component was **not working**:
- 100% of extractions were from EntityRuler (pattern matching)
- 0% from statistical NER (trained model)

**This has been fixed** in the pipeline_synthesis_2025-11-18 run.

### Current Results (pipeline_synthesis_2025-11-18)

The NER union (spaCy + V2) now captures IUPHAR entities:

| Entity | Papers Found | Papers |
|--------|--------------|--------|
| iuphar-db | 6 | 22674159, 23087376, 24234439, 26464438, 31691834, + others |
| iuphar | 4 | Multiple papers |
| gtopdb | 3 | 26464438, 31691834, + others |
| bps | 3 | Multiple papers |

### Papers Now Captured in Set C Union

| PMID | In Set C Union | Status |
|------|---------------|--------|
| 22674159 | ✅ | linguistic_setfit_agree |
| 23087376 | ✅ | linguistic_setfit_agree |
| 24234439 | ✅ | linguistic_setfit_agree |
| 26464438 | ✅ | linguistic_setfit_agree |
| 31691834 | ✅ | linguistic_setfit_agree |
| 29149325 | ❌ | Not in query (MeSH gap) |
| 34718737 | ❌ | Not in query (MeSH gap) |

**Improvement**: 5 of 7 key papers now captured (vs 2 in original 2022 inventory).

---

## 6. Alias/Deduplication Gap

### The Rebranding Problem

The resource was rebranded:
- **2012**: IUPHAR-DB
- **2014+**: Guide to PHARMACOLOGY / GtoPdb

### Current Entity Inventory

In `set_c_entity_inventory.csv`, these appear as **separate entries**:
- `iuphar-db` (6 papers)
- `gtopdb` (3 papers)
- `guide to pharmacology` (papers)

These are all the **same resource** but not linked.

**Recommendation**: Implement alias resolution to merge:
- IUPHAR-DB = Guide to PHARMACOLOGY = GtoPdb = IUPHAR/BPS Guide to PHARMACOLOGY

---

## 7. Summary of Issues

| Issue | Impact | Status | Fix |
|-------|--------|--------|-----|
| Missing MeSH term | 2 key papers not in query | Open | Add `Databases, Pharmaceutical` |
| V2 NER failure on 24234439 | 2014 paper had no entities | Fixed | NER union captures it now |
| Statistical NER broken | Lower recall | Fixed | Fixed in pipeline_synthesis |
| No alias linking | Resource appears fragmented | Open | Need alias resolution |

---

## 8. Recommendations

### Immediate Actions

1. **Add MeSH term to query**:
   ```
   MESH:"Databases, Pharmaceutical"
   ```
   This will capture PMID 29149325 (2,391 citations) and 34718737.

2. **Create alias mapping** for IUPHAR variants:
   ```
   iuphar-db → guide_to_pharmacology
   gtopdb → guide_to_pharmacology
   iuphar/bps guide to pharmacology → guide_to_pharmacology
   ```

### Long-term Improvements

1. **Rebranding detection**: Flag papers that describe resource renaming/rebranding
2. **URL-based linking**: Papers sharing same URL should be linked
3. **Citation-based ranking**: Prioritize high-citation papers in review

---

## 9. Data Files Reference

| File | Description |
|------|-------------|
| `data/epmc_query_results_2022.csv` | Original 2022 query (21,678 papers) |
| `data/final_inventory_2022.csv` | Original 2022 inventory (3,113 resources) |
| `collab_results/2025-10-24-s4985d_2022_rerun/` | 2025 rerun with V2 NER |
| `pipeline_synthesis_2025-11-18/data/paper_sets/set_c_union.csv` | Updated paper set |
| `pipeline_synthesis_2025-11-18/data/entity_inventories/set_c_entity_inventory.csv` | NER union entities |
| `config/final_query_v5.1_wildcards_fixed.txt` | Current query template |

---

## 10. Conclusion

The IUPHAR-DB investigation revealed multiple pipeline stages contributing to underrepresentation:

1. **Query stage**: Missing MeSH term excludes most-cited papers
2. **NER stage**: V2 model failed on rebranding paper (now fixed with NER union)
3. **Deduplication stage**: Rebranded names not linked as aliases

The updated pipeline (pipeline_synthesis_2025-11-18) captures **5 of 7** key papers. The remaining 2 require a query modification to include `Databases, Pharmaceutical` MeSH term.

---

**Report Generated**: 2025-12-10
**Investigation Context**: GBC Biodata Inventory Pipeline
