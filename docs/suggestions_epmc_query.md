This is a solid starting query. You have correctly identified the core components: a URL indicator, a "type" indicator (database/resource), and strong noise reduction (excluding standard repositories and clinical trials).

To expand this for better recall—while trying to maintain reasonable precision—you need to broaden the "synonyms" for what constitutes a bioresource and add typical phrases authors use when introducing them.

Here is an analysis of your current query and suggested expansions.

### 1\. Analysis of Current Query Strength/Weaknesses

  * **Strengths:** Excellent exclusion list. removing `github`, `zenodo`, `figshare`, and `clinical trials` is crucial, otherwise, you will just get papers that *share code* or *register a study* rather than papers that *are* a database resource.
  * **Weaknesses:**
      * **Type keywords are too narrow:** You only use `data OR resource OR database*`. You are missing many common terms for bio-websites (e.g., "portal", "knowledgebase", "atlas").
      * **Missing "Availability" signals:** Papers describing new resources almost always use specific phrasing in the abstract like "freely available at" or "accessible online".

-----

### 2\. Suggested Expansions

#### A. Broaden Resource "Type" Keywords

Authors often use specific branding for their resources. Add these to your positive inclusion criteria:

  * `repository`
  * `knowledgebase` OR `"knowledge base"`
  * `portal`
  * `atlas` (common for single-cell data now)
  * `platform` (often used for integrated data/tools)
  * `"web server"` (often a tool, but frequently a front-end for a biological dataset)
  * `biobank`

#### B. Add "Availability" Phrasing

Often the strongest signal isn't just the presence of "http" and "database", but the *introductory phrase* used to share it.

  * `"freely available"`
  * `"publicly available"`
  * `"accessible at"`
  * `"available online"`

### 3\. Revised EPMC Query

Here is a broadened version. I have moved the key "Type" indicators to search both `TITLE` and `ABSTRACT` (searching TITLE for these keywords is a very strong positive signal).

```lucene
(
  (ABSTRACT:(www OR http* OR ftp)) 
  AND 
  (
    TITLE:(database* OR repository OR "knowledge base" OR knowledgebase OR atlas OR portal OR biobank OR "web server" OR resource)
    OR 
    ABSTRACT:(database* OR repository OR "knowledge base" OR knowledgebase OR atlas OR portal OR biobank OR "web server" OR "freely available" OR "publicly available" OR "accessible at" OR "available online")
  )
) 
NOT (TITLE:(retract* OR withdraw* OR erratum)) 
NOT (ABSTRACT:(retract* OR withdraw* OR erratum OR github.* OR cran.r OR youtube.com OR bitbucket.org OR links.lww.com OR osf.io OR bioconductor.org OR annualreviews.org OR creativecommons.org OR sourceforge.net OR bit.ly OR zenodo OR onlinelibrary.wiley.com OR proteomecentral.proteomexchange.org/dataset OR oxfordjournals.org/nar/database OR figshare OR mendeley OR .pdf OR "clinical trial" OR registration OR "trial registration" OR clinicaltrial OR "registration number" OR pre-registration OR preregistration)) 
AND (SRC:(MED OR PMC OR AGR OR CBA)) 
AND (FIRST_PDATE:[{0} TO {1}])
```

### Key Changes Explained:

1.  **Added `ftp`:** older bioresources sometimes still use FTP for bulk data.
2.  **Split Keyword Targeting:** I have set generic resource keywords to look in `TITLE OR ABSTRACT`. If "Atlas" is in the title, it's almost certainly relevant.
3.  **Added Availability Phrases:** Included `"accessible at"`, etc., in the Abstract search.

### A Note on Risks (The "GitHub" Problem)

You currently exclude `github.*`.

  * **The Benefit:** You avoid thousands of papers that just share their analysis code.
  * **The Risk:** Many modern, smaller bioresources (especially in bioinformatics) now use **GitHub Pages** (e.g., `username.github.io/toolname`) as their primary "website." By strictly excluding GitHub, you might miss these smaller, newer resources.
  * **Recommendation:** If you want *absolute maximum* recall, you might need to remove `github.*` from the NOT list, but be prepared for a massive increase in noise (false positives). If you want established databases, keep it excluded.
