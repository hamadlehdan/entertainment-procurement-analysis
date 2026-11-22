# Source, definitions and audit requirements

**Source:** UK Cabinet Office, [Contracts Finder published notices in OCDS JSON](https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search). [Official government guidance and documentation](https://www.gov.uk/government/publications/open-contracting). Licence: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).

**Scope:** The script requests award-stage notices inside an explicit, bounded **publication** date window. It screens titles and descriptions with case-insensitive keyword categories in `src/analyse.py`. This is a sample of *relevant terms* and does **not** exhaustively identify all AV or entertainment procurement. Check matched titles manually before conclusions.

**Grain:** One row per `(ocid, award_id)`, retaining the last published release for duplicates. Award value is counted once for each award, even if it names several suppliers. Multiple awards within one procurement remain separate.

**Amounts:** `amount_gbp` uses published `awards[*].value.amount` only when `currency='GBP'`, with no assumed FX conversion. Missing and non-GBP values are excluded from money summaries but included in the screened-award count and the quality file.

**Quality controls:** fixed query interval; API page count; explicit failure on pagination cap or loop; no silent truncation; duplicate award IDs; source notice URL; distinct buyer, supplier and segments; missing values; multi-supplier awards.

**Limits:** Published maximum/estimated/committed awards are not verified expenditure, profitability, hourly rates, costs saved or realised invoices. Text matching may introduce false matches. These are public third-party records; the author was not involved in award decisions.
