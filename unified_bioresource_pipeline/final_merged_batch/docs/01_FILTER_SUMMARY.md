# Step 1: URL Filtering Summary

**Generated:** 2025-12-10 10:39:55

## Overview

Filtering both bioresource inventory batches to include only resources with live URLs (HTTP status 200).

---

## Results

| Batch | Input | Live URLs | Filtered Out | Retention |
|-------|-------|-----------|--------------|-----------|
| 2010-2022 | 1,688 | 996 | 692 | 59.0% |
| 2022-2025 | 1,510 | 1,510 | 0 | 100.0% |
| **Total** | **3,198** | **2,506** | **692** | **78.4%** |

---

## Filtered Records by Status (2010-2022 batch)

| Status | Count |
|--------|-------|
| 404 | 81 |
| 403 | 68 |
| 405 | 23 |
| 503 | 21 |
| 500 | 10 |
| 502 | 10 |
| 406 | 5 |
| 400 | 4 |
| 465 | 3 |
| 410 | 3 |

---

## Sample Filtered Records (2010-2022 batch - first 10)

| best_name | extracted_url | status |
|-----------|---------------|--------|
| PLAZA | http://bioinformatics.psb.ugent.be/plaza/versions/ | 404 |
| OCHEM | http://ochem.eu | HTTPConnectionPool(host='ochem.eu', port=80): Max retries exceeded with url: / (Caused by ConnectTim |
| IMGT | http://www.imgt.org | HTTPConnectionPool(host='www.imgt.org', port=80): Max retries exceeded with url: / (Caused by Connec |
| Therapeutic Target Database | http://bidd.nus.edu.sg/group/ttd/ttd.asp | HTTPConnectionPool(host='bidd.nus.edu.sg', port=80): Max retries exceeded with url: /group/ttd/ttd.a |
| miRBase | http://www.mirbasetracker.org | HTTPConnectionPool(host='www.mirbasetracker.org', port=80): Max retries exceeded with url: / (Caused |
| ClinVar | http://simple-clinvar.broadinstitute.org/ | HTTPSConnectionPool(host='simple-clinvar.broadinstitute.org', port=443): Max retries exceeded with u |
| EURISCO | http://eurisco.ecpgr.org | 404 |
| DCDB | http://www.cls.zju.edu.cn/dcdb/ | 403 |
| GTDB | https://www.biosino.org/gtdb/ | 403 |
| OryzaPG | http://oryzapg.iab.keio.ac.jp/ | HTTPConnectionPool(host='oryzapg.iab.keio.ac.jp', port=80): Max retries exceeded with url: / (Caused |

---

## Output Files

- `data/filtered/batch_2010_2022_live.csv` (996 records)
- `data/filtered/batch_2022_2025_live.csv` (1,510 records)

---

## Ready for Step 2?

Review the above statistics. If satisfied with the filtering results, proceed to deduplication:

```bash
python scripts/02_identify_duplicates.py
```
