# Entertainment Procurement | Public Contract Awards Analysis

**Business question:** How much public-sector contract-award activity is visible for music, live events and audiovisual services, and which buyers and service segments appear in the records?

**Real source:** UK government's [Contracts Finder OCDS award notice feed](https://www.contractsfinder.service.gov.uk/Published/Notices/OCDS/Search), licensed under the [Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). This project uses *actual published awards*, not fictitious suppliers or confidential employer contracts.

## What this project produces
- Reproducible, fixed-window downloads from the official UK procurement API.
- A transparent keyword-defined segment classification with traceable notice URLs.
- Deduplicated award-level figures; separate GBP amount and supplier-count fields.
- Interactive dashboard: segment mix, largest buyers and award-value distribution.
- Ranked awards, audit CSV, Markdown management findings and automated tests.

## Run
In Terminal, from the repository directory:

```bash
python3 -m pip install -r requirements.txt
python3 src/analyse.py --from-date 2026-01-01 --to-date 2026-01-31
python3 -m pytest -q tests
```

The script fetches the original source when run and saves `outputs/dashboard.html`, `outputs/findings.md`, `outputs/screened_awards.csv` and table CSVs. A network connection is required; the script refuses to generate misleading results when the source is inaccessible or pagination is truncated. To widen scope, extend the publication window and adjust `--max-pages` so the API can be read fully.

## Key definitions and honest limitations
- **Award value** = disclosed contract-award amount, **not** paid spend, savings, profit or supplier quote.
- **One award** is counted once even when it names multiple suppliers.
- **Relevant awards** = textual keyword matches, not a comprehensive market total. False positives require review.
- The analysis represents public third-party records and makes no claim of participation in procurement decisions.

**Skills:** sourcing and cleaning public operational data · contract-value aggregation · supplier/buyer context · data-quality controls · visual business reports. See [methods and source notes](docs/SOURCE_NOTES.md).

**Employer-facing takeaway:** Such analysis can support early market mapping and supplier research, but operational supplier selection additionally requires quality, specifications, timing, warranty, safety and total-cost information.
