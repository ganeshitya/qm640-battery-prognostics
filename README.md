# QM640 Capstone — Early-Life Prediction of Lithium-Ion Battery Cycle Life

**Walsh College · QM640: Data Analytics Capstone**

Predicting the eventual cycle life of lithium-ion cells from data confined to their
first 100 charge–discharge cycles, and decomposing lifetime variance into the portion
attributable to the charging protocol versus intrinsic cell-to-cell variation.

This repository holds all ingestion code, harmonisation scripts, engineered feature
tables, model definitions and analysis notebooks for the project. It is the
open-access companion to the project synopsis in [`docs/`](docs/).

---

## Research questions

| RQ | Question | Test |
|----|----------|------|
| **RQ1** | Can a classifier using only cycles 2–100 separate short-life (< 550 cycles) from long-life (≥ 550) cells with accuracy above the 0.85 benchmark? | One-sample *z* test for a proportion |
| **RQ2** | Does a 1D-CNN + BiLSTM on the raw ΔQ(V) curve beat a feature-engineered regularised baseline? | McNemar χ² on discordant pairs; DeLong on paired AUC |
| **RQ3** | Does a gradient-boosted ensemble cut mean absolute percentage error by ≥ 3 pp against the elastic-net baseline? | Welch two-sample *t* on per-cell APE |
| **RQ4** | What share of capacity-fade-rate variance is between-protocol rather than within-protocol? | Likelihood ratio test on nested multilevel models; bootstrap CI on ICC |

**Design sample size: 171 cells** (binding constraint, RQ3). **Corpus assembled: 235 cells** — 37% headroom.

---

## Data sources

All five sources are openly published and downloadable without registration.
Raw archives are **downloaded, not redistributed** — see [Reproduction](#reproduction).

| Source | Cells | Chemistry | Format | URL |
|--------|-------|-----------|--------|-----|
| MIT–Stanford–TRI (Severson et al., 2019) | 124 | LFP / graphite | 18650 | https://data.matr.io/1/ |
| MIT–Stanford–TRI (Attia et al., 2020) | 45 | LFP / graphite | 18650 | https://data.matr.io/1/ |
| NASA PCoE Battery Data Set | 34 | LCO / NCA | 18650 | https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/ |
| CALCE, Univ. of Maryland (CS2, CX2) | 24 | LCO | Prismatic pouch | https://calce.umd.edu/battery-data |
| Oxford Battery Degradation Dataset 1 | 8 | LCO / NCO | Pouch | https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac |
| **Total** | **235** | | | |

End of life is redefined uniformly across all sources as the first cycle at which
discharge capacity falls below 80% of nominal. NASA cells terminated at 70% are
flagged as right-censored via the `censored` column.

---

## Data dictionary

The machine-readable dictionary — including types, units, permissible ranges and
null-handling rules for all 26 variables — is versioned at
**[`data/dictionary.yaml`](data/dictionary.yaml)**.

The harmonised analysis table is stored at two levels, joined on `cell_id`:

- `data/processed/cell_level.parquet` — 235 rows, one per cell
- `data/processed/cycle_level.parquet` — ~180,000 rows, one per cell-cycle

---

## Repository structure

```
qm640-battery-prognostics/
├── Makefile                      make data | features | models | report
├── environment.yml               pinned Python 3.11 environment
├── data/
│   ├── raw/                      downloaded archives (git-ignored)
│   ├── interim/                  harmonised per-source Parquet
│   ├── processed/                cell_level.parquet, cycle_level.parquet
│   ├── dictionary.yaml           machine-readable data dictionary
│   └── checksums.sha256          integrity manifest for raw archives
├── src/
│   ├── ingest/                   one loader per source repository
│   ├── harmonise/                schema mapping, voltage-grid resampling, EOL rule
│   ├── features/                 ΔQ(V) moments, fade slope, thermal and IR features
│   ├── models/                   rq1_classify · rq2_deep · rq3_regress · rq4_multilevel
│   └── evaluate/                 nested CV, bootstrap intervals, Holm correction
├── notebooks/                    01_eda … 05_results
├── results/                      figures, metric tables, fitted model artefacts
└── docs/                         synopsis, final report, decision-aid one-pager
```

---

## Reproduction

```bash
git clone https://github.com/ganeshitya/qm640-battery-prognostics.git
cd qm640-battery-prognostics
conda env create -f environment.yml
conda activate qm640

make data        # download source archives and verify checksums
make features    # harmonise schemas and build the feature table
make models      # fit RQ1–RQ4 under nested cross-validation
make report      # regenerate all figures and metric tables
```

`make data` reports which archives require a manual download step (the TRI, CALCE
and Oxford custodians serve files behind interstitial pages); the landing page for
each is printed with the expected destination path.

---

## Project status

| Week | Milestone | Status |
|------|-----------|--------|
| 1–2 | Source acquisition and ingestion layer | In progress |
| 3 | Schema harmonisation, 235-cell corpus | Planned |
| 4 | Feature engineering and EDA | Planned |
| 5–6 | RQ1 classifier family | Planned |
| 6–7 | RQ2 deep model and paired tests | Planned |
| 7–8 | RQ3 regression family and SHAP | Planned |
| 9 | RQ4 multilevel models and ICC | Planned |
| 10 | Synthesis and final report | Planned |

---

## Licence and attribution

Code in this repository is released under the [MIT Licence](LICENSE).

Source data remains the property of the originating laboratories and is subject to
their own terms. Any use of this work must cite the underlying datasets:

- Severson, K. A., et al. (2019). Data-driven prediction of battery cycle life before
  capacity degradation. *Nature Energy, 4*(5), 383–391.
- Attia, P. M., et al. (2020). Closed-loop optimization of fast-charging protocols for
  batteries with machine learning. *Nature, 578*(7795), 397–402.
- Saha, B., & Goebel, K. (2007). *Battery data set*. NASA Ames Prognostics Data Repository.
- CALCE Battery Research Group, University of Maryland. *Battery data*.
- Howey, D., & Birkl, C. (2017). *Oxford battery degradation dataset 1*. University of Oxford.

Methodological reference for the sample size and power calculations:

- Gelman, A., & Hill, J. (2007). *Data analysis using regression and
  multilevel/hierarchical models*. Cambridge University Press.
