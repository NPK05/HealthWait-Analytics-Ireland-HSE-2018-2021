# Healthcare Waiting List Analytics

### Ireland Health Service Executive (HSE) \| 2018--2021

Healthcare waiting lists are a critical indicator of pressure within
national healthcare systems. Long waiting times delay treatment, worsen
patient outcomes, and create operational inefficiencies.

This project analyzes Ireland's **Health Service Executive (HSE)**
national waiting list dataset from **2018--2021** to identify demand
patterns, specialties with the largest backlog, and systemic bottlenecks
affecting healthcare access.

The analysis combines **Python-based exploratory data analysis,
statistical testing, and SQL queries** to transform operational
healthcare data into actionable insights.

------------------------------------------------------------------------

# Project Overview

**Objective**

Analyze national healthcare waiting lists to understand:

-   How waiting lists evolved over time
-   Which specialties carry the largest backlog
-   What factors contribute to long waiting durations
-   How demographic patterns influence healthcare demand

------------------------------------------------------------------------

# Project Snapshot

  Metric                        Value
  ----------------------------- --------------------------
  Total Patient Waits           **24,640,969**
  Inpatient Records             **182,136**
  Outpatient Records            **270,808**
  Total Analytical Records      **452,944**
  Specialties Tracked           **78**
  Specialty Groups              **27**
  Patients Waiting 18+ Months   **4,582,271 (18.6%)**
  Analysis Period               **Jan 2018 -- Mar 2021**

------------------------------------------------------------------------

# Data Pipeline

Insert image: `charts/data_pipeline_workflow.png`

Pipeline stages:

1.  Raw CSV ingestion
2.  Data cleaning and normalization
3.  Data transformation
4.  Exploratory data analysis
5.  Statistical testing
6.  Visualization generation
7.  Dashboard reporting

------------------------------------------------------------------------

# Data Architecture

Insert image: `charts/01_data_model.png`

Key tables:

-   `fact_inpatient`
-   `fact_outpatient`
-   `dim_specialty`
-   `vw_waiting_list_full`

------------------------------------------------------------------------

# Waiting List Growth Trends

Insert image: `charts/02_volume_trends.png`

Waiting lists increased steadily across the analysis period, with a
significant rise during the **COVID‑19 pandemic in 2020**.

------------------------------------------------------------------------

# Waiting Time Distribution

Insert image: `charts/04_time_band_analysis.png`

Key insight:

-   **20% of outpatient patients wait longer than 18 months**
-   **8.3% of inpatient patients exceed this threshold**

This suggests that **specialist consultation capacity is the main
bottleneck**.

------------------------------------------------------------------------

# Specialties Driving the Backlog

Insert image: `charts/05_top_specialties.png`

Top specialties contributing to waiting lists:

-   Orthopaedics
-   ENT (Otolaryngology)
-   Dermatology
-   Ophthalmology
-   General Surgery

------------------------------------------------------------------------

# Specialty Risk Analysis

Insert image: `charts/10_specialty_risk_matrix.png`

ENT services demonstrate the highest long‑wait risk with roughly **32%
of patients waiting longer than 18 months**.

------------------------------------------------------------------------

# Demographic Insights

Insert image: `charts/08_demographics.png`

Key findings:

-   Adults represent **85.5% of waiting list demand**
-   Children represent a larger share of outpatient services
-   The **65+ population segment is growing fastest**

------------------------------------------------------------------------

# COVID‑19 Impact

Insert image: `charts/07_covid_impact.png`

Between **March 2020 and March 2021**, the number of patients waiting
longer than **18 months more than doubled**.

------------------------------------------------------------------------

# Statistical Analysis

Insert image: `charts/09_statistical_analysis.png`

Statistical tests confirm:

-   Significant differences across years
-   Structural differences between inpatient and outpatient systems
-   A statistically significant upward trend in waiting durations

------------------------------------------------------------------------

# Executive Insights Dashboard

Insert image: `charts/dashboard_preview.png`

The dashboard enables interactive exploration of:

-   Waiting list trends
-   Specialty demand
-   Demographic patterns
-   Long‑wait risk areas

------------------------------------------------------------------------

# Key Insights

-   Outpatient services account for **88% of total waiting list volume**
-   ENT and Orthopaedics represent the **largest backlog drivers**
-   COVID‑19 significantly increased long waiting durations
-   Aging population trends will continue increasing healthcare demand

------------------------------------------------------------------------

# Business Recommendations

**Expand outpatient consultation capacity**

Improving specialist consultation throughput could reduce the largest
source of waiting list growth.

**Prioritize high‑risk specialties**

Additional resources should focus on ENT, Orthopaedics, and
Ophthalmology.

**Implement predictive monitoring**

Automated dashboards tracking long‑wait percentages could enable earlier
intervention.

**Improve healthcare data integration**

Linking waiting list data with hospital episode records would unlock
deeper predictive analytics.

------------------------------------------------------------------------

# Project Structure

    HealthWait-Analytics-Ireland-HSE-2018-2021

    data/
    raw datasets

    charts/
    visualizations

    sql/
    database schema and analytical queries

    healthcare_eda_analysis.py
    EDA and statistical analysis

    healthcare_eda_queries.sql
    SQL queries

    healthcare_eda_dashboard.html
    interactive dashboard

    healthcare_eda_report.docx
    full analytical report

------------------------------------------------------------------------

# Tools & Technologies

Python\
Pandas\
NumPy\
Matplotlib\
Seaborn\
SciPy\
Scikit‑Learn\
SQL

------------------------------------------------------------------------

# Future Improvements

-   Build Power BI / Tableau dashboard
-   Add predictive wait time forecasting
-   Integrate geographic hospital data
-   Perform patient‑level cohort analysis

------------------------------------------------------------------------

# Author

**Pavan Kumar**

GitHub\
https://github.com/NPK05
