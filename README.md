# 18 Months Too Long — Ireland HSE Waiting List Analytics (2018–2021)

> *EDA of Ireland's HSE waiting lists (2018–2021) — 24.6M patient-waits, COVID impact analysis, statistical testing & interactive analytics dashboard.*

<br>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white)
![Chart.js](https://img.shields.io/badge/Dashboard-Chart.js-FF6384?style=flat&logo=chartdotjs&logoColor=white)
![HTML](https://img.shields.io/badge/Frontend-HTML%2FCSS%2FJS-E34F26?style=flat&logo=html5&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-10B981?style=flat)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat)

<br>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Business Problem](#-business-problem)
- [Dataset](#-dataset)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Data Cleaning](#-data-cleaning)
- [Data Model](#-data-model)
- [Key Findings](#-key-findings)
- [Statistical Analysis](#-statistical-analysis)
- [Visualisations](#-visualisations)
- [Interactive Dashboard](#-interactive-dashboard)
- [SQL Queries](#-sql-queries)
- [Recommendations](#-recommendations)
- [How to Run](#-how-to-run)
- [Author](#-author)

---

## 🏥 Project Overview

This project is a comprehensive **Exploratory Data Analysis (EDA)** of Ireland's Health Service Executive (HSE) national waiting lists from **January 2018 to March 2021**. The analysis covers **452,944 records** representing **24.6 million patient-waits** across 78 medical specialties for both Inpatient and Outpatient case types.

The project delivers:
- Full EDA with descriptive statistics, hypothesis testing, and correlation analysis
- 10 publication-quality visualisation charts (PNG)
- A complete SQL data model with 15+ analytical queries
- An interactive multi-tab HTML analytics dashboard
- 6 evidence-based actionable recommendations for HSE policymakers

---

## ❗ Business Problem

Ireland's healthcare system faced a mounting waiting list crisis across 2018–2021. This analysis was conducted to answer five critical questions:

| # | Business Question |
|---|-------------------|
| 1 | **How large is the crisis?** What is the true scale of waiting list volumes and long-wait rates? |
| 2 | **What did COVID-19 do?** How did the March 2020 lockdown impact waiting lists and is the backlog still growing? |
| 3 | **Where are resources misallocated?** Is planning aligned with actual Inpatient vs Outpatient demand? |
| 4 | **Which specialties are failing patients?** Which groups have the highest proportion of 18+ month waits? |
| 5 | **Who is most at risk?** Are children and elderly patients disproportionately affected? |

---

## 📦 Dataset

| Attribute | Detail |
|-----------|--------|
| **Source** | Health Service Executive (HSE) Ireland — [data.gov.ie](https://data.gov.ie) |
| **Files** | `IN_WL 2018–2021.csv` · `Op_WL 2018–2021.csv` · `Mapping_Specialty.csv` |
| **Period** | January 2018 – March 2021 *(2021 is partial: Jan–Mar only)* |
| **Total Records** | 452,944 rows |
| **Inpatient Records** | 182,136 |
| **Outpatient Records** | 270,808 |
| **Total Patient-Waits** | 24,640,969 |
| **Specialties** | 78 specialties mapped to 27 groups |

### Key Fields

| Field | Description |
|-------|-------------|
| `Archive_Date` | Monthly snapshot date |
| `Group` | Hospital group name |
| `Hospital_HIPE` | Hospital identifier code |
| `Specialty_Name` | Clinical specialty |
| `Case_Type` | Inpatient / Day Case / Outpatient |
| `Time_Bands` | Wait duration band (0–3 Mo through 18+ Mo) |
| `Total` | Number of patients in that band |
| `Age_Categorisation` | 0–15 / 16–64 / 65+ |

### Time Bands

```
0–3 Months  →  3–6 Months  →  6–9 Months  →  9–12 Months
12–15 Months  →  15–18 Months  →  18+ Months (CRISIS THRESHOLD)
```

---

## 📁 Project Structure

```
hse-waiting-list-eda/
│
├── data/
│   ├── IN_WL 2018-2021.csv          # Inpatient waiting list data
│   ├── Op_WL 2018-2021.csv          # Outpatient waiting list data
│   └── Mapping_Specialty.csv        # Specialty → Group mapping
│
├── notebooks/
│   └── healthcare_eda_analysis.py   # Full EDA Python script
│
├── sql/
│   └── healthcare_eda_queries.sql   # DDL + 15 analytical queries
│
├── charts/
│   ├── 01_data_model.png            # Entity Relationship Diagram
│   ├── 02_volume_trends.png         # Annual bar + monthly area
│   ├── 03_descriptive_stats.png     # Histograms, box plots, stats table
│   ├── 04_time_band_analysis.png    # Wait duration breakdown
│   ├── 05_top_specialties.png       # Top 10 horizontal bars
│   ├── 06_specialty_heatmap.png     # Normalised annual load heatmap
│   ├── 07_covid_impact.png          # 4-panel COVID analysis
│   ├── 08_demographics.png          # Age/type donuts + stacked bar
│   ├── 09_statistical_analysis.png  # Violin plots, Spearman, Chi-square
│   └── 10_specialty_risk_matrix.png # Bubble scatter: volume vs risk
│
├── dashboard/
│   └── healthcare_eda_dashboard.html  # Interactive analytics dashboard
│
├── report/
│   └── healthcare_eda_report.docx   # Full 10-section Word report
│
└── README.md
```

---

## 🛠 Tech Stack

| Layer | Tools |
|-------|-------|
| **Data Analysis** | Python 3.10+, Pandas, NumPy |
| **Statistical Testing** | SciPy (Kruskal-Wallis, Mann-Whitney U, Chi-Square, Spearman, Pearson) |
| **Visualisation** | Matplotlib, Seaborn |
| **Database** | SQL (PostgreSQL-compatible DDL) |
| **Dashboard** | HTML5, CSS3, Vanilla JavaScript, Chart.js 4.4 |
| **Typography** | Plus Jakarta Sans, JetBrains Mono |
| **Reporting** | Python-docx (Word report) |

---

## 🧹 Data Cleaning

The raw dataset required the following cleaning steps before analysis:

```python
# 1. Strip leading/trailing whitespace from all string columns
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

# 2. Fix column name typo in Outpatient file
op_df.rename(columns={'Speciality_Name': 'Specialty_Name'}, inplace=True)

# 3. Normalise time band inconsistencies
df['Time_Bands'] = df['Time_Bands'].str.replace(r'^\s+', '', regex=True)
df['Time_Bands'] = df['Time_Bands'].replace('18 Months +', '18+ Months')

# 4. Remove trailing empty column in Inpatient file
ip_df = pd.read_csv('IN_WL.csv', usecols=lambda x: not x.startswith('Unnamed'))

# 5. Parse dates correctly (Irish format: day first)
df['Archive_Date'] = pd.to_datetime(df['Archive_Date'], dayfirst=True)
```

**Issues found and resolved:**

| Issue | Resolution |
|-------|-----------|
| Leading/trailing whitespace in all string fields | `str.strip()` applied to all object columns |
| Outpatient column typo `Speciality_Name` | Renamed to `Specialty_Name` |
| Time band inconsistencies (leading spaces, `"18 Months +"`) | Regex normalisation |
| Trailing empty column `Unnamed: 8` in Inpatient | Excluded via `usecols` lambda |
| Date parsing failure | `dayfirst=True` applied |
| 191 missing HIPE codes | Retained with null flag; excluded from HIPE-level analysis |

---

## 🗄 Data Model

```
dim_specialty (PK: specialty_name)
        ↑
        └── LEFT JOIN on specialty_name
                ┌────────────────────────┐
  fact_inpatient ──┤                        ├── UNION ALL → vw_waiting_list_full
 fact_outpatient ──┘                        │
                                            └── Used for all cross-type analysis
```

Unmatched specialties from the mapping file default to `specialty_group = 'Other'`.

---

## 🔍 Key Findings

### Volume & Scale

| Metric | Value |
|--------|-------|
| Total patient-waits 2018–2021 | **24,640,969** |
| Inpatient total | 2,905,230 (11.8%) |
| Outpatient total | 21,735,739 **(88.2%)** |
| Patients waiting 18+ months | **4,582,271 (18.6%)** |

### COVID Impact (2019 → 2020)

| Metric | Change |
|--------|--------|
| Outpatient volume | +5.9% |
| Inpatient volume | **+11.5%** |
| 18+ month inpatient waiters | **+121% in 12 months** |
| Monthly 18+ mo waiters (Mar 2020) | 5,105 |
| Monthly 18+ mo waiters (Mar 2021) | **11,306** |

> ⚠️ The backlog was still accelerating at the data cut-off in March 2021.

### Specialty Risk (18+ Month Wait Rate)

| Specialty Group | 18+ Month Rate | Risk Level |
|----------------|---------------|------------|
| ENT | **32.0%** | 🔴 HIGH |
| Eyes | 24.6% | 🔴 HIGH |
| Urine | 22.1% | 🔴 HIGH |
| Cosmetic | 22.1% | 🔴 HIGH |
| Skin | 20.2% | 🟡 MEDIUM |
| Bones | 20.1% | 🟡 MEDIUM |
| Brain | 21.1% | 🟡 MEDIUM |

### Demographics

| Metric | Inpatient | Outpatient |
|--------|-----------|------------|
| Adult share | 90.4% | 84.9% |
| Child (0–15) share | 9.6% | **15.1%** |
| 65+ cohort growth 2018–2020 | — | **+19%** |

---

## 📊 Statistical Analysis

All distributions exhibited extreme right-skewness (skewness > 5.4, kurtosis > 53), making non-parametric testing the appropriate approach.

### Descriptive Statistics

| Metric | Inpatient | Outpatient | Combined |
|--------|-----------|------------|---------|
| N (records) | 182,136 | 270,808 | 452,944 |
| Sum | 2,905,230 | 21,735,739 | 24,640,969 |
| Mean | 15.95 | 80.21 | 54.38 |
| Median | 5.0 | 29.0 | 13.0 |
| Std Dev | 30.99 | 148.62 | 120.78 |
| Skewness | 5.655 | 5.474 | 6.686 |
| Kurtosis | 55.58 | 53.36 | 79.81 |
| CV% | 194.3% | 185.3% | 222.1% |

### Hypothesis Tests

| Test | Statistic | p-value | Conclusion |
|------|-----------|---------|-----------|
| **Kruskal-Wallis H** (Total by Year) | H = 141.4 | p < 0.001 | ✅ Significant year-to-year differences |
| **Mann-Whitney U** (IP vs OP) | U = 1.34×10¹⁰ | p ≈ 0.000 | ✅ IP and OP distributions significantly differ |
| **Chi-Square** (Age Group × Time Bands) | χ² = 2015.7 | p < 0.001 | ✅ Significant but weak effect (Cramér's V = 0.067) |
| **Spearman ρ** (Year vs Avg Wait Rank) | ρ = 0.194 | p = 0.001 | ✅ Confirmed upward deterioration trend |
| **Pearson r** (Specialty Total vs Avg Wait) | r = 0.114 | p = 0.068 | ⚠️ Marginal — not significant at α=0.05 |

### Key Correlations

| Variables | Correlation | Interpretation |
|-----------|-------------|----------------|
| Total ↔ Records | +0.917 | Strongest relationship — scale drives record count |
| Year ↔ Total | −0.149 | Weak negative |
| Year ↔ Avg Wait | −0.123 | Marginal — avg wait worsening over years |
| Total ↔ Avg Wait | +0.114 | Marginal |
| Year ↔ Wait Rank (Spearman ρ) | **+0.194** | Significant deterioration trend |

---

## 📈 Visualisations

| Chart | Description |
|-------|-------------|
| `01_data_model.png` | Entity Relationship Diagram |
| `02_volume_trends.png` | Annual bar chart + monthly stacked area timeline |
| `03_descriptive_stats.png` | Distribution histograms, box plots, stats comparison table |
| `04_time_band_analysis.png` | Wait duration band breakdown — IP vs OP |
| `05_top_specialties.png` | Top 10 specialties by volume — horizontal bar |
| `06_specialty_heatmap.png` | Normalised annual patient load heatmap across groups |
| `07_covid_impact.png` | 4-panel COVID impact analysis (before/after lockdown) |
| `08_demographics.png` | Adult/child donut charts + age-group stacked bar |
| `09_statistical_analysis.png` | Violin plots, Spearman trend line, Chi-square residuals |
| `10_specialty_risk_matrix.png` | Bubble scatter: total volume vs 18+ month risk rate |

---

## 🖥 Interactive Dashboard

The project includes a fully self-contained **interactive HTML dashboard** (`healthcare_eda_dashboard.html`) — no server required, open directly in any browser.

### Dashboard Tabs

| Tab | Contents |
|-----|----------|
| 📋 **About & Dataset** | Business problem, dataset metadata, key metrics |
| ⊞ **Overview** | Summary banner, annual volumes, patient type split, monthly timeline |
| 📈 **Time Trends** | Monthly line charts, 18+ month crisis trend, wait band profiles |
| 🏥 **Specialties** | Top 10 bar charts (IP & OP), searchable risk table |
| 👥 **Demographics** | Adult/child donuts, age group stacked bar, growth trends |
| ⚗️ **Statistics** | Descriptive stats table, hypothesis test results, correlations |
| 💡 **Insights** | 9 critical data-driven findings with statistical evidence |
| 🎯 **Recommendations** | 6 prioritised, evidence-based policy actions |

### Features
- 🔍 Live specialty search filter
- 📊 14 interactive Chart.js charts with tooltips
- 👤 Click **NPK05** chip or sidebar avatar → contact modal (email + LinkedIn)
- 📱 Responsive layout · No build step · No dependencies beyond CDN

---

## 🗃 SQL Queries

The file `healthcare_eda_queries.sql` contains:

- Full DDL: `dim_specialty`, `fact_inpatient`, `fact_outpatient` tables
- View: `vw_waiting_list_full` (unified IP + OP)
- **15+ analytical queries** including:

```sql
-- Example: Top specialties by 18+ month rate
SELECT
    specialty_group,
    SUM(total) AS total_patients,
    SUM(CASE WHEN time_band = '18+ Months' THEN total ELSE 0 END) AS long_waiters,
    ROUND(100.0 * SUM(CASE WHEN time_band = '18+ Months' THEN total ELSE 0 END)
          / SUM(total), 1) AS long_wait_pct
FROM vw_waiting_list_full
GROUP BY specialty_group
ORDER BY long_wait_pct DESC;
```

---

## 💡 Recommendations

| Priority | Recommendation | Evidence |
|----------|---------------|----------|
| 🔴 CRITICAL | **Declare a National 18+ Month Emergency** — surge capacity in ENT, Eyes, Bones via private sector contracts and extended theatre hours | 4.58M patients · ENT 32% rate |
| 🟠 HIGH | **COVID Backlog Recovery Plan** — specialty-specific quarterly targets modelled on NHS Elective Recovery Framework | +121% in 12 months |
| 🔵 OPERATIONAL | **Realign Resources to Actual Demand** — 88.2% of waits are Outpatient; planning must shift away from inpatient bed-count focus | 21.7M OP waits |
| 🟢 EQUITY | **Ring-Fence Paediatric Capacity** — dedicated 12-month target for children with ring-fenced consultant sessions | 15.1% of OP waits are children |
| 🟣 MONITORING | **Automated Monthly KPI Alerting** — deploy ±5% MoM threshold alerts per specialty group | Spearman ρ=0.194 (p=0.001) |
| ⚫ DATA OPS | **Fix Data Gaps & Enable Patient-Level Linkage** — resolve 191 missing HIPE codes; link to hospital episode statistics | 191 nulls · no patient IDs |

---

## ▶ How to Run

### Prerequisites

```bash
pip install pandas numpy matplotlib seaborn scipy python-docx
```

### Run the EDA Script

```bash
# Clone the repository
git clone https://github.com/nallabothulapavankumar/hse-waiting-list-eda.git
cd hse-waiting-list-eda

# Place data files in the /data folder
# Run the full analysis
python notebooks/healthcare_eda_analysis.py
```

This will generate:
- All 10 PNG charts in `/charts/`
- The Word report in `/report/`

### View the Dashboard

```bash
# No server needed — just open in browser
open dashboard/healthcare_eda_dashboard.html
```

Or simply double-click the HTML file in your file explorer.

### Run SQL Queries

```bash
# Load schema and queries into PostgreSQL
psql -U your_user -d your_db -f sql/healthcare_eda_queries.sql
```

---

## 👤 Author

**Nallabothula Pavan Kumar (NPK05)**

Data Analyst · HSE Ireland Waiting List EDA Portfolio Project

[![Email](https://img.shields.io/badge/Email-npavankumarus72%40gmail.com-EA4335?style=flat&logo=gmail&logoColor=white)](mailto:npavankumarus72@gmail.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-nallabothulapavankumar-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/nallabothulapavankumar/)

---

## 📄 License

This project is licensed under the MIT License. The dataset is sourced from [HSE Ireland Open Data](https://data.gov.ie) and is publicly available under the Creative Commons Attribution 4.0 licence.

---

> *"Behind every number in this dataset is a patient — a person waiting in pain, uncertainty, or diminishing hope. Data analysis is only meaningful when it leads to action."*
>
> — NPK05
