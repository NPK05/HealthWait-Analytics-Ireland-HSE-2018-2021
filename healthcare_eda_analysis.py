"""
=============================================================================
 HEALTHCARE WAITING LIST — ADVANCED EDA
 Ireland HSE National Waiting List Data  |  2018 – 2021
 Portfolio Project  |  Senior Data Analyst
=============================================================================
 Files Used:
   - Data/Inpatient/IN_WL 2018-2021.csv      (4 files)
   - Data/Outpatient/Op_WL 2018-2021.csv     (4 files)
   - Data/Mapping_Specialty.csv              (1 lookup)
=============================================================================
"""

# ─── IMPORTS ─────────────────────────────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from scipy import stats
from scipy.stats import (chi2_contingency, kruskal, mannwhitneyu,
                         pearsonr, spearmanr)
from sklearn.preprocessing import StandardScaler
import warnings
import os
import json
warnings.filterwarnings('ignore')

# ─── PATHS ───────────────────────────────────────────────────────────────────
DATA_ROOT  = '/home/claude/healthcare_data/Data'
OUTPUT_DIR = '/mnt/user-data/outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── STYLE ───────────────────────────────────────────────────────────────────
BG        = '#07080F'
SURFACE   = '#0F1219'
BORDER    = '#1C2333'
CYAN      = '#00D4FF'
RED       = '#FF4060'
GOLD      = '#FFB800'
GREEN     = '#00E676'
PURPLE    = '#B06AFF'
MUTED     = '#4A5568'
TEXT      = '#D0D8E8'

PALETTE = [CYAN, RED, GOLD, GREEN, PURPLE, '#FF8C42', '#74B9FF', '#FD79A8', '#55EFC4', '#FFEAA7']

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor':   SURFACE,
    'axes.edgecolor':   BORDER,
    'axes.labelcolor':  TEXT,
    'axes.titlecolor':  '#FFFFFF',
    'xtick.color':      MUTED,
    'ytick.color':      MUTED,
    'text.color':       TEXT,
    'grid.color':       BORDER,
    'grid.alpha':       0.7,
    'font.family':      'DejaVu Sans',
    'axes.titlesize':   12,
    'axes.labelsize':   10,
    'figure.titlesize': 14,
    'axes.spines.top':  False,
    'axes.spines.right':False,
})

TIME_ORDER = [
    '0-3 Months', '3-6 Months', '6-9 Months', '9-12 Months',
    '12-15 Months', '15-18 Months', '18+ Months'
]

def save(fig, name):
    path = os.path.join(OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f'  [SAVED] {name}')
    return path

def fmt_m(x, _=None):
    if x is None or (isinstance(x, float) and np.isnan(x)): return ""
    if x >= 1e6:  return f'{x/1e6:.1f}M'
    if x >= 1e3:  return f'{x/1e3:.0f}K'
    return str(int(x))

# =============================================================================
# SECTION 1 — DATA INGESTION & CLEANING
# =============================================================================
print('\n' + '='*65)
print('  SECTION 1: DATA INGESTION & CLEANING')
print('='*65)

def load_inpatient():
    frames = []
    for yr in [2018, 2019, 2020, 2021]:
        path = f'{DATA_ROOT}/Inpatient/IN_WL {yr}.csv'
        df = pd.read_csv(path, usecols=lambda c: 'Unnamed' not in c)
        df['Year'] = yr
        frames.append(df)
    df_all = pd.concat(frames, ignore_index=True)
    df_all.columns = df_all.columns.str.strip()
    return df_all

def load_outpatient():
    frames = []
    for yr in [2018, 2019, 2020, 2021]:
        path = f'{DATA_ROOT}/Outpatient/Op_WL {yr}.csv'
        df = pd.read_csv(path)
        df['Year'] = yr
        frames.append(df)
    df_all = pd.concat(frames, ignore_index=True)
    df_all.columns = df_all.columns.str.strip()
    df_all.rename(columns={'Speciality': 'Specialty_Name'}, inplace=True)
    return df_all

ip  = load_inpatient()
op  = load_outpatient()
lkp = pd.read_csv(f'{DATA_ROOT}/Mapping_Specialty.csv')
lkp.columns = lkp.columns.str.strip()

# ── Strip string fields
for df in [ip, op, lkp]:
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()

# ── Parse dates
ip['Archive_Date'] = pd.to_datetime(ip['Archive_Date'], dayfirst=True)
op['Archive_Date'] = pd.to_datetime(op['Archive_Date'], dayfirst=True)

ip['YearMonth'] = ip['Archive_Date'].dt.to_period('M')
op['YearMonth'] = op['Archive_Date'].dt.to_period('M')
ip['Month'] = ip['Archive_Date'].dt.month
op['Month'] = op['Archive_Date'].dt.month

# ── Merge specialty mapping (data model join)
ip = ip.merge(lkp, left_on='Specialty_Name', right_on='Specialty', how='left')
op = op.merge(lkp, left_on='Specialty_Name', right_on='Specialty', how='left')
ip['Specialty Group'] = ip['Specialty Group'].fillna('Other')
op['Specialty Group'] = op['Specialty Group'].fillna('Other')

# ── Drop rows missing critical demographic fields
op = op.dropna(subset=['Age_Profile'])

# ── Tag patient type
ip['Patient_Type'] = 'Inpatient'
op['Patient_Type'] = 'Outpatient'

# ── Combined dataset
COMMON = ['Archive_Date', 'Year', 'Month', 'YearMonth',
          'Specialty_Name', 'Specialty Group', 'Adult_Child',
          'Age_Profile', 'Time_Bands', 'Total', 'Patient_Type']

combined = pd.concat([ip[COMMON], op[COMMON]], ignore_index=True)

# ── Wait band numeric mapping (for statistical analysis)
WAIT_MAP = {t: i for i, t in enumerate(TIME_ORDER)}
combined['Wait_Rank'] = combined['Time_Bands'].map(WAIT_MAP)
ip['Wait_Rank']       = ip['Time_Bands'].map(WAIT_MAP)
op['Wait_Rank']       = op['Time_Bands'].map(WAIT_MAP)

print(f'\n  Inpatient  rows   : {len(ip):>10,}')
print(f'  Outpatient rows   : {len(op):>10,}')
print(f'  Combined rows     : {len(combined):>10,}')
print(f'  Inpatient  total  : {ip["Total"].sum():>10,}')
print(f'  Outpatient total  : {op["Total"].sum():>10,}')
print(f'  Grand total       : {combined["Total"].sum():>10,}')
print(f'  Date range        : {combined["Archive_Date"].min().date()} → {combined["Archive_Date"].max().date()}')
print(f'  Specialties       : {combined["Specialty_Name"].nunique()}')
print(f'  Specialty Groups  : {combined["Specialty Group"].nunique()}')

# Missing value audit
print('\n  --- MISSING VALUE AUDIT ---')
for name, df in [('Inpatient', ip), ('Outpatient', op), ('Combined', combined)]:
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        print(f'  {name}: {nulls.to_dict()}')
    else:
        print(f'  {name}: No missing values in key columns')

# =============================================================================
# SECTION 2 — DESCRIPTIVE STATISTICS
# =============================================================================
print('\n' + '='*65)
print('  SECTION 2: DESCRIPTIVE STATISTICS')
print('='*65)

def full_desc(series, label):
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return {
        'Dataset':         label,
        'N (records)':     len(s),
        'Sum':             int(s.sum()),
        'Mean':            round(s.mean(), 3),
        'Median':          round(s.median(), 3),
        'Mode':            int(s.mode()[0]),
        'Std Dev':         round(s.std(), 3),
        'Variance':        round(s.var(), 3),
        'Min':             int(s.min()),
        'Max':             int(s.max()),
        'Range':           int(s.max() - s.min()),
        'Q1':              round(q1, 3),
        'Q3':              round(q3, 3),
        'IQR':             round(iqr, 3),
        'P5':              round(s.quantile(0.05), 3),
        'P95':             round(s.quantile(0.95), 3),
        'P99':             round(s.quantile(0.99), 3),
        'CV (%)':          round(s.std() / s.mean() * 100, 2),
        'Skewness':        round(s.skew(), 4),
        'Kurtosis':        round(s.kurtosis(), 4),
        'Outliers (IQR)':  int(((s < q1 - 1.5*iqr) | (s > q3 + 1.5*iqr)).sum()),
    }

stat_ip  = full_desc(ip['Total'],       'Inpatient')
stat_op  = full_desc(op['Total'],       'Outpatient')
stat_all = full_desc(combined['Total'], 'Combined')

desc_df = pd.DataFrame([stat_ip, stat_op, stat_all]).set_index('Dataset')
print('\n', desc_df.T.to_string())

# Annual totals
print('\n  --- ANNUAL TOTALS ---')
annual = combined.groupby(['Year', 'Patient_Type'])['Total'].sum().unstack()
print(annual.to_string())

# YoY change
print('\n  --- YEAR-OVER-YEAR CHANGE ---')
for pt in ['Inpatient', 'Outpatient']:
    t = combined[combined['Patient_Type'] == pt].groupby('Year')['Total'].sum()
    yoy = t.pct_change() * 100
    for yr, val in yoy.dropna().items():
        print(f'  {pt} {yr-1}→{yr}: {val:+.1f}%')

# =============================================================================
# SECTION 3 — ADVANCED STATISTICAL TESTS
# =============================================================================
print('\n' + '='*65)
print('  SECTION 3: ADVANCED STATISTICAL ANALYSIS')
print('='*65)

# Kruskal-Wallis: does Total differ by Year?
groups_by_year = [combined[combined['Year'] == y]['Total'].values for y in [2018, 2019, 2020, 2021]]
kw_h, kw_p = kruskal(*groups_by_year)
print(f'\n  Kruskal-Wallis (Total ~ Year):')
print(f'    H = {kw_h:.4f}  |  p = {kw_p:.4e}  |  {"SIGNIFICANT" if kw_p < 0.05 else "NOT SIGNIFICANT"}')

# Mann-Whitney: Inpatient vs Outpatient
mw_u, mw_p = mannwhitneyu(ip['Total'], op['Total'], alternative='two-sided')
print(f'\n  Mann-Whitney U (Inpatient vs Outpatient):')
print(f'    U = {mw_u:.0f}  |  p = {mw_p:.4e}  |  {"SIGNIFICANT" if mw_p < 0.05 else "NOT SIGNIFICANT"}')

# Chi-Square: Adult_Child vs Time_Bands
ct_table = pd.crosstab(combined['Adult_Child'], combined['Time_Bands'])
chi2_val, chi2_p, chi2_dof, _ = chi2_contingency(ct_table)
cramers_v = np.sqrt(chi2_val / (ct_table.values.sum() * (min(ct_table.shape) - 1)))
print(f'\n  Chi-Square (Adult_Child × Time_Bands):')
print(f'    χ² = {chi2_val:.2f}  |  p = {chi2_p:.4e}  |  df = {chi2_dof}')
print(f'    Cramér\'s V = {cramers_v:.4f}  ({"Strong" if cramers_v>0.3 else "Moderate" if cramers_v>0.1 else "Weak"} association)')

# Spearman: Year vs average wait rank
avg_wait = combined.groupby('Year')['Wait_Rank'].mean()
sp_r, sp_p = spearmanr(avg_wait.index, avg_wait.values)
print(f'\n  Spearman ρ (Year vs Avg Wait Rank):')
print(f'    ρ = {sp_r:.4f}  |  p = {sp_p:.4e}  |  {"Upward trend SIGNIFICANT" if sp_p < 0.05 else "No significant trend"}')

# Pearson: Total vs Wait_Rank at specialty-year level
spec_yr = combined.groupby(['Specialty_Name', 'Year']).agg(
    Total=('Total', 'sum'),
    AvgWait=('Wait_Rank', 'mean')
).reset_index().dropna()
pr, pp = pearsonr(spec_yr['Total'], spec_yr['AvgWait'])
print(f'\n  Pearson r (Specialty Total vs Avg Wait):')
print(f'    r = {pr:.4f}  |  p = {pp:.4e}')

# Correlation matrix
corr_num = spec_yr[['Year', 'Total', 'AvgWait']].corr()
print(f'\n  Correlation Matrix (Specialty-Year level):')
print(corr_num.round(4).to_string())

# =============================================================================
# SECTION 4 — DATA MODEL (HOW TABLES CONNECT)
# =============================================================================
print('\n' + '='*65)
print('  SECTION 4: DATA MODEL')
print('='*65)
print("""
  TABLE RELATIONSHIPS:
  ─────────────────────────────────────────────────────────────
  dim_specialty (mapping)
    PK: specialty_name (varchar)
      └─ specialty_group (varchar)

  fact_inpatient (IN_WL 2018–2021 combined)
    FK: specialty_name → dim_specialty.specialty_name
    Columns: archive_date, specialty_hipe, case_type,
             adult_child, age_profile, time_bands, total, year

  fact_outpatient (Op_WL 2018–2021 combined)
    FK: specialty_name → dim_specialty.specialty_name
    Columns: archive_date, specialty_hipe, adult_child,
             age_profile, time_bands, total, year

  Join type: LEFT JOIN (preserves all records even if specialty
             not found in mapping — filled as 'Other')

  Combined fact view (used for cross-analysis):
    UNION ALL of fact_inpatient + fact_outpatient
    with patient_type tag ('Inpatient' / 'Outpatient')
  ─────────────────────────────────────────────────────────────
""")

# =============================================================================
# SECTION 5 — VISUALISATIONS (12 charts)
# =============================================================================
print('\n' + '='*65)
print('  SECTION 5: GENERATING CHARTS')
print('='*65)

# ── Chart 1: Data Model / Entity Relationship Diagram ─────────────────────
fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
ax.set_facecolor(BG); ax.axis('off')

def draw_table(ax, x, y, title, fields, title_color, w=2.8, h_row=0.38):
    n = len(fields)
    h = h_row * (n + 1.5)
    # header
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h_row*1.5,
        boxstyle='round,pad=0.02', fc=title_color, ec='none', zorder=3))
    ax.text(x + w/2, y + h_row*0.75, title, ha='center', va='center',
            fontsize=10, fontweight='bold', color='white', zorder=4)
    # body
    ax.add_patch(mpatches.FancyBboxPatch((x, y - h_row*n), w, h_row*n,
        boxstyle='round,pad=0.02', fc=SURFACE, ec=title_color, linewidth=1.5, zorder=2))
    for i, (col, tag, is_key) in enumerate(fields):
        row_y = y - h_row*(i+0.5)
        key_sym = '🔑 ' if is_key == 'PK' else '🔗 ' if is_key == 'FK' else '   '
        tag_col = GOLD if is_key == 'PK' else CYAN if is_key == 'FK' else MUTED
        ax.text(x + 0.15, row_y, key_sym + col, va='center', fontsize=8,
                color=TEXT if is_key else MUTED, zorder=4)
        ax.text(x + w - 0.15, row_y, tag, va='center', ha='right', fontsize=7,
                color=tag_col, zorder=4)
    return (x + w/2, y + h_row*0.75), (x + w/2, y - h_row*n)  # top, bottom centres

ax.set_xlim(0, 14); ax.set_ylim(-4, 2)

# DIM_SPECIALTY
draw_table(ax, 5.5, 1.4, 'dim_specialty', [
    ('specialty_name', 'VARCHAR', 'PK'),
    ('specialty_group', 'VARCHAR', None),
], PURPLE)

# FACT_INPATIENT
draw_table(ax, 0.3, 0.8, 'fact_inpatient', [
    ('archive_date',  'DATE',    None),
    ('specialty_name','VARCHAR', 'FK'),
    ('specialty_hipe','INT',     None),
    ('case_type',     'VARCHAR', None),
    ('adult_child',   'VARCHAR', None),
    ('age_profile',   'VARCHAR', None),
    ('time_bands',    'VARCHAR', None),
    ('total',         'INT',     None),
    ('year',          'INT',     None),
], CYAN)

# FACT_OUTPATIENT
draw_table(ax, 10.8, 0.8, 'fact_outpatient', [
    ('archive_date',  'DATE',    None),
    ('specialty_name','VARCHAR', 'FK'),
    ('specialty_hipe','INT',     None),
    ('adult_child',   'VARCHAR', None),
    ('age_profile',   'VARCHAR', None),
    ('time_bands',    'VARCHAR', None),
    ('total',         'INT',     None),
    ('year',          'INT',     None),
], RED)

# COMBINED VIEW
draw_table(ax, 5.5, -1.8, 'vw_combined_waitlist', [
    ('archive_date',   'DATE',    None),
    ('specialty_name', 'VARCHAR', None),
    ('specialty_group','VARCHAR', None),
    ('adult_child',    'VARCHAR', None),
    ('age_profile',    'VARCHAR', None),
    ('time_bands',     'VARCHAR', None),
    ('total',          'INT',     None),
    ('patient_type',   'VARCHAR', None),
    ('year',           'INT',     None),
], GOLD)

# Arrows
def arrow(ax, x1, y1, x2, y2, color):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.8))

# FK joins to dim_specialty
arrow(ax, 1.7, 0.8, 5.7, 0.78, CYAN)
arrow(ax, 13.0, 0.8, 8.3, 0.78, RED)

# UNION ALL to view
arrow(ax, 3.05, -1.1, 6.4, -1.8, GOLD)
arrow(ax, 11.1, -1.1, 8.0, -1.8, GOLD)

ax.text(3.3,  0.95, 'LEFT JOIN\non specialty_name', ha='center', fontsize=7.5, color=CYAN)
ax.text(10.7, 0.95, 'LEFT JOIN\non specialty_name', ha='center', fontsize=7.5, color=RED)
ax.text(4.5,  -1.4, 'UNION ALL', ha='center', fontsize=7.5, color=GOLD)
ax.text(9.0,  -1.4, 'UNION ALL', ha='center', fontsize=7.5, color=GOLD)

ax.text(7.0, 1.75, 'DATA MODEL — ENTITY RELATIONSHIP DIAGRAM',
        ha='center', fontsize=13, fontweight='bold', color='white')
ax.text(7.0, 1.52, 'Ireland HSE Healthcare Waiting List  |  2018–2021',
        ha='center', fontsize=9, color=MUTED)

# Legend
for i, (sym, label) in enumerate([('🔑', 'Primary Key'), ('🔗', 'Foreign Key'), ('→', 'JOIN / UNION ALL')]):
    ax.text(0.4, -3.4 + i*0.38, f'{sym}  {label}', fontsize=8, color=MUTED)

fig.tight_layout(pad=1)
save(fig, '01_data_model.png')

# ── Chart 2: Annual Volumes + Monthly Trend ────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 7), facecolor=BG)
fig.suptitle('Waiting List Volume Overview  |  Annual & Monthly Trends',
             fontsize=13, color='white', y=1.01)

# Left: grouped bar annual
ax = axes[0]; ax.set_facecolor(SURFACE)
ann = combined.groupby(['Year', 'Patient_Type'])['Total'].sum().unstack()
x = np.arange(4); w = 0.35
b1 = ax.bar(x - w/2, ann['Inpatient']/1e6,  w, color=CYAN, alpha=0.9, label='Inpatient',  zorder=3)
b2 = ax.bar(x + w/2, ann['Outpatient']/1e6, w, color=RED,  alpha=0.9, label='Outpatient', zorder=3)
ax.set_xticks(x); ax.set_xticklabels([2018, 2019, 2020, 2021])
ax.set_ylabel('Patients (Millions)'); ax.set_title('Annual Volume by Patient Type')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
ax.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax.grid(axis='y', zorder=0)
for b in list(b1)+list(b2):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02,
            f'{b.get_height():.2f}M', ha='center', va='bottom', fontsize=8, color=TEXT)

# Right: monthly stacked area
ax2 = axes[1]; ax2.set_facecolor(SURFACE)
monthly = combined.groupby(['YearMonth', 'Patient_Type'])['Total'].sum().unstack().fillna(0)
months_str = [str(p) for p in monthly.index]
xi = np.arange(len(months_str))
ax2.fill_between(xi, monthly.get('Outpatient', 0)/1e6, alpha=0.55, color=RED,   label='Outpatient')
ax2.fill_between(xi, monthly.get('Inpatient',  0)/1e6, alpha=0.80, color=CYAN,  label='Inpatient')
step = max(1, len(months_str)//8)
ax2.set_xticks(xi[::step]); ax2.set_xticklabels(months_str[::step], rotation=30, ha='right', fontsize=8)
ax2.set_title('Monthly Trend  |  COVID Lockdown Marked')
ax2.set_ylabel('Patients (Millions)')
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
ax2.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax2.grid(alpha=0.4)
covid = months_str.index('2020-03') if '2020-03' in months_str else None
if covid:
    ax2.axvline(covid, color=GOLD, lw=2, linestyle='--', alpha=0.9)
    ax2.text(covid+0.6, ax2.get_ylim()[1]*0.88, 'COVID-19\nMar 2020',
             fontsize=8, color=GOLD, va='top')

plt.tight_layout()
save(fig, '02_volume_trends.png')

# ── Chart 3: Descriptive Statistics Dashboard ──────────────────────────────
fig = plt.figure(figsize=(18, 11), facecolor=BG)
fig.suptitle('Descriptive Statistics Dashboard', fontsize=13, color='white')
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.38)

# 3a: IP distribution histogram
ax1 = fig.add_subplot(gs[0, 0]); ax1.set_facecolor(SURFACE)
ip_clip = ip['Total'].clip(upper=ip['Total'].quantile(0.98))
ax1.hist(ip_clip, bins=50, color=CYAN, alpha=0.85, edgecolor='none', zorder=3)
ax1.axvline(ip['Total'].mean(),   color=GOLD, lw=2, ls='--', label=f'Mean={ip["Total"].mean():.1f}', zorder=4)
ax1.axvline(ip['Total'].median(), color=RED,  lw=2, ls=':',  label=f'Median={ip["Total"].median():.0f}', zorder=4)
ax1.set_title('Inpatient Total — Distribution', color='white')
ax1.set_xlabel('Patients per Record'); ax1.set_ylabel('Frequency')
ax1.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)
ax1.grid(axis='y', zorder=0)

# 3b: OP distribution histogram
ax2 = fig.add_subplot(gs[0, 1]); ax2.set_facecolor(SURFACE)
op_clip = op['Total'].clip(upper=op['Total'].quantile(0.98))
ax2.hist(op_clip, bins=50, color=RED, alpha=0.85, edgecolor='none', zorder=3)
ax2.axvline(op['Total'].mean(),   color=GOLD, lw=2, ls='--', label=f'Mean={op["Total"].mean():.1f}', zorder=4)
ax2.axvline(op['Total'].median(), color=CYAN, lw=2, ls=':',  label=f'Median={op["Total"].median():.0f}', zorder=4)
ax2.set_title('Outpatient Total — Distribution', color='white')
ax2.set_xlabel('Patients per Record'); ax2.set_ylabel('Frequency')
ax2.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)
ax2.grid(axis='y', zorder=0)

# 3c: Box plot by year
ax3 = fig.add_subplot(gs[0, 2]); ax3.set_facecolor(SURFACE)
bp_data = [np.log1p(combined[combined['Year'] == y]['Total'].values) for y in [2018, 2019, 2020, 2021]]
bp = ax3.boxplot(bp_data, patch_artist=True, notch=True,
                  medianprops=dict(color='white', lw=2.5),
                  whiskerprops=dict(color=MUTED, lw=1.2),
                  capprops=dict(color=MUTED, lw=1.2),
                  flierprops=dict(marker='.', markersize=2, alpha=0.3, color=MUTED))
colors_bp = [CYAN, GREEN, GOLD, RED]
for patch, c in zip(bp['boxes'], colors_bp):
    patch.set_facecolor(c); patch.set_alpha(0.75)
ax3.set_xticklabels([2018, 2019, 2020, 2021])
ax3.set_title('Log(Total) Distribution by Year', color='white')
ax3.set_ylabel('log(Total + 1)'); ax3.grid(axis='y', alpha=0.4)

# 3d: Stats table (bottom row spanning all cols)
ax4 = fig.add_subplot(gs[1, :]); ax4.set_facecolor(BG); ax4.axis('off')
rows = [
    ['N (records)',    f"{stat_ip['N (records)']:,}",      f"{stat_op['N (records)']:,}",    f"{stat_all['N (records)']:,}"],
    ['Total Patients', f"{stat_ip['Sum']:,}",              f"{stat_op['Sum']:,}",            f"{stat_all['Sum']:,}"],
    ['Mean',           f"{stat_ip['Mean']}",               f"{stat_op['Mean']}",             f"{stat_all['Mean']}"],
    ['Median',         f"{stat_ip['Median']}",             f"{stat_op['Median']}",           f"{stat_all['Median']}"],
    ['Mode',           f"{stat_ip['Mode']}",               f"{stat_op['Mode']}",             f"{stat_all['Mode']}"],
    ['Std Dev',        f"{stat_ip['Std Dev']}",            f"{stat_op['Std Dev']}",          f"{stat_all['Std Dev']}"],
    ['CV (%)',         f"{stat_ip['CV (%)']}%",            f"{stat_op['CV (%)']}%",          f"{stat_all['CV (%)']}%"],
    ['Skewness',       f"{stat_ip['Skewness']}",           f"{stat_op['Skewness']}",         f"{stat_all['Skewness']}"],
    ['Kurtosis',       f"{stat_ip['Kurtosis']}",           f"{stat_op['Kurtosis']}",         f"{stat_all['Kurtosis']}"],
    ['IQR',            f"{stat_ip['IQR']}",                f"{stat_op['IQR']}",              f"{stat_all['IQR']}"],
    ['P5 / P95',       f"{stat_ip['P5']} / {stat_ip['P95']}", f"{stat_op['P5']} / {stat_op['P95']}", f"{stat_all['P5']} / {stat_all['P95']}"],
    ['Outliers (IQR)', f"{stat_ip['Outliers (IQR)']:,}",  f"{stat_op['Outliers (IQR)']:,}", f"{stat_all['Outliers (IQR)']:,}"],
]
t = ax4.table(cellText=rows, colLabels=['Metric', 'Inpatient', 'Outpatient', 'Combined'],
              cellLoc='center', loc='center', bbox=[0.05, 0.02, 0.9, 0.92])
t.auto_set_font_size(False); t.set_fontsize(9.5)
for (r, c), cell in t.get_celld().items():
    if r == 0:
        cell.set_facecolor(CYAN); cell.set_text_props(color=BG, fontweight='bold')
    else:
        cell.set_facecolor(SURFACE if r % 2 == 0 else '#141A27')
        cell.set_text_props(color=TEXT if c > 0 else MUTED)
    cell.set_edgecolor(BORDER)

save(fig, '03_descriptive_stats.png')

# ── Chart 4: Time Band Analysis ────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor=BG)
fig.suptitle('Waiting Duration Breakdown  |  Time Band Analysis', fontsize=13, color='white', y=1.01)
tb_colors = [GREEN, GREEN, GOLD, GOLD, RED, RED, '#CC0033']

for ax, (df, label) in zip(axes, [(ip, 'Inpatient'), (op, 'Outpatient')]):
    ax.set_facecolor(SURFACE)
    tb = df.groupby('Time_Bands')['Total'].sum().reindex(TIME_ORDER).fillna(0)
    pct = tb / tb.sum() * 100
    bars = ax.bar(range(len(tb)), pct.values, color=tb_colors, alpha=0.9, edgecolor='none', zorder=3)
    ax.set_xticks(range(len(tb))); ax.set_xticklabels(TIME_ORDER, rotation=32, ha='right')
    ax.set_ylabel('% of Total Patients'); ax.set_title(f'{label} — Wait Duration %')
    ax.grid(axis='y', zorder=0)
    for bar, val in zip(bars, pct.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{val:.1f}%', ha='center', fontsize=8.5, color='white', va='bottom')
    lw_pct = pct.get('18+ Months', 0)
    ax.text(0.97, 0.96, f'18+ Months: {lw_pct:.1f}%', transform=ax.transAxes,
            ha='right', va='top', fontsize=9, color=RED,
            bbox=dict(boxstyle='round,pad=0.4', fc=SURFACE, ec=RED, alpha=0.9))

plt.tight_layout()
save(fig, '04_time_band_analysis.png')

# ── Chart 5: Top Specialties ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(18, 9), facecolor=BG)
fig.suptitle('Top 10 Specialties by Waiting List Volume', fontsize=13, color='white', y=1.01)

for ax, (df, label, color) in zip(axes,
        [(ip, 'Inpatient', CYAN), (op, 'Outpatient', RED)]):
    ax.set_facecolor(SURFACE)
    top10 = df.groupby('Specialty_Name')['Total'].sum().nlargest(10).sort_values()
    bars  = ax.barh(range(len(top10)), top10.values / 1e6, color=color, alpha=0.85, edgecolor='none')
    ax.set_yticks(range(len(top10))); ax.set_yticklabels(top10.index, fontsize=9)
    ax.set_xlabel('Total Patients (Millions)'); ax.set_title(f'{label} — Top 10')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))
    ax.grid(axis='x', zorder=0)
    for bar, val in zip(bars, top10.values):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f'{val/1e6:.2f}M', va='center', fontsize=8, color=TEXT)

plt.tight_layout()
save(fig, '05_top_specialties.png')

# ── Chart 6: Specialty Heatmap ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(20, 10), facecolor=BG)
fig.suptitle('Specialty Heatmap — Normalised Annual Load', fontsize=13, color='white')

cmap_hc = LinearSegmentedColormap.from_list('hc', [BG, '#003566', CYAN, GOLD, RED])

for ax, (df, label) in zip(axes, [(ip, 'Inpatient'), (op, 'Outpatient')]):
    ax.set_facecolor(SURFACE)
    top15 = df.groupby('Specialty_Name')['Total'].sum().nlargest(15).index
    pivot = df[df['Specialty_Name'].isin(top15)].groupby(
        ['Specialty_Name', 'Year'])['Total'].sum().unstack()
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
    pivot_norm = pivot.div(pivot.max(axis=1), axis=0)
    sns.heatmap(pivot_norm, ax=ax, cmap=cmap_hc, linewidths=0.4, linecolor=BG,
                annot=pivot.map(fmt_m), fmt='',
                annot_kws={'size': 7, 'color': 'white'},
                cbar_kws={'label': 'Normalised Load', 'shrink': 0.7})
    ax.set_title(f'{label} — Top 15 Specialties', color='white')
    ax.set_xlabel('Year'); ax.set_ylabel('')
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_color(MUTED)
    cbar.ax.tick_params(colors=MUTED)

plt.tight_layout()
save(fig, '06_specialty_heatmap.png')

# ── Chart 7: COVID-19 Impact Analysis ─────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12), facecolor=BG)
fig.suptitle('COVID-19 Impact Analysis  |  Disruption & Backlog Formation', fontsize=13, color='white')

# 7a: Long-wait trend
ax1 = axes[0, 0]; ax1.set_facecolor(SURFACE)
lw = combined[combined['Time_Bands'] == '18+ Months'].groupby(
    ['YearMonth', 'Patient_Type'])['Total'].sum().unstack().fillna(0)
xi = np.arange(len(lw))
for col, color in [('Inpatient', CYAN), ('Outpatient', RED)]:
    if col in lw.columns:
        vals = lw[col].replace(0, np.nan)
        ax1.plot(xi, vals / 1e3, color=color, lw=2.5, label=col)
        ax1.fill_between(xi, (vals / 1e3).fillna(0), alpha=0.12, color=color)
months_lw = [str(m) for m in lw.index]
step = max(1, len(months_lw)//7)
ax1.set_xticks(xi[::step]); ax1.set_xticklabels(months_lw[::step], rotation=30, ha='right', fontsize=8)
ax1.set_title('18+ Month Wait Trend (COVID Backlog)', color='white')
ax1.set_ylabel("Patients ('000)"); ax1.grid(alpha=0.4)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}K'))
ax1.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)

# 7b: YoY delta by specialty group
ax2 = axes[0, 1]; ax2.set_facecolor(SURFACE)
g19 = combined[combined['Year'] == 2019].groupby('Specialty Group')['Total'].sum()
g20 = combined[combined['Year'] == 2020].groupby('Specialty Group')['Total'].sum()
delta = ((g20 - g19) / g19 * 100).dropna().sort_values()
delta = delta[abs(delta) > 0.1].head(18)
col_d = [RED if v > 0 else GREEN for v in delta.values]
ax2.barh(range(len(delta)), delta.values, color=col_d, alpha=0.9, edgecolor='none')
ax2.set_yticks(range(len(delta))); ax2.set_yticklabels(delta.index, fontsize=8)
ax2.axvline(0, color=TEXT, lw=1)
ax2.set_title('2019→2020 YoY Change by Specialty Group (%)', color='white')
ax2.set_xlabel('% Change'); ax2.grid(axis='x', alpha=0.4)

# 7c: Pre vs COVID age group bar
ax3 = axes[1, 0]; ax3.set_facecolor(SURFACE)
pre  = combined[combined['Year'].isin([2018, 2019])].groupby('Age_Profile')['Total'].sum()
post = combined[combined['Year'].isin([2020, 2021])].groupby('Age_Profile')['Total'].sum()
ages = sorted(set(pre.index) | set(post.index))
xi2 = np.arange(len(ages)); w = 0.35
ax3.bar(xi2 - w/2, [pre.get(a, 0)/1e6 for a in ages], w, color=CYAN,   alpha=0.9, label='Pre-COVID (2018-19)')
ax3.bar(xi2 + w/2, [post.get(a, 0)/1e6 for a in ages], w, color=GOLD,  alpha=0.9, label='COVID Era (2020-21)')
ax3.set_xticks(xi2); ax3.set_xticklabels(ages)
ax3.set_title('Age Group Load: Pre-COVID vs COVID Era', color='white')
ax3.set_ylabel('Patients (Millions)'); ax3.grid(axis='y', alpha=0.4)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}M'))
ax3.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)

# 7d: Monthly inpatient only with rolling avg
ax4 = axes[1, 1]; ax4.set_facecolor(SURFACE)
ip_monthly = ip.groupby('YearMonth')['Total'].sum()
xi3 = np.arange(len(ip_monthly))
ax4.plot(xi3, ip_monthly.values / 1e3, color=CYAN, lw=1.5, alpha=0.5, label='Monthly')
roll = pd.Series(ip_monthly.values).rolling(3, center=True).mean()
ax4.plot(xi3, roll / 1e3, color=GREEN, lw=2.5, label='3-Month Rolling Avg')
step3 = max(1, len(xi3)//8)
ax4.set_xticks(xi3[::step3])
ax4.set_xticklabels([str(m) for m in ip_monthly.index[::step3]], rotation=30, ha='right', fontsize=8)
ax4.set_title('Inpatient Monthly Total + Rolling Average', color='white')
ax4.set_ylabel("Patients ('000)"); ax4.grid(alpha=0.4)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}K'))
ax4.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
if covid:
    ax4.axvline(covid, color=GOLD, lw=1.8, ls='--')
    ax4.text(covid+0.5, ax4.get_ylim()[1]*0.92, 'COVID', fontsize=8, color=GOLD)

plt.tight_layout()
save(fig, '07_covid_impact.png')

# ── Chart 8: Demographic Analysis ─────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12), facecolor=BG)
fig.suptitle('Demographic Analysis  |  Age, Adult vs Child', fontsize=13, color='white')

# 8a: Adult/Child donut IP
ax1 = axes[0, 0]; ax1.set_facecolor(SURFACE)
ac_ip = ip.groupby('Adult_Child')['Total'].sum()
wedges, _, autotexts = ax1.pie(
    ac_ip.values, labels=ac_ip.index, autopct='%1.1f%%', startangle=90,
    colors=[CYAN, RED], wedgeprops={'edgecolor': BG, 'linewidth': 2.5},
    textprops={'color': TEXT, 'fontsize': 10})
for at in autotexts:
    at.set_color(BG); at.set_fontweight('bold')
centre = plt.Circle((0, 0), 0.55, color=SURFACE)
ax1.add_patch(centre)
ax1.text(0, 0, 'Inpatient', ha='center', va='center', fontsize=10, color=TEXT, fontweight='bold')
ax1.set_title('Inpatient — Adult vs Child', color='white')

# 8b: Adult/Child donut OP
ax2 = axes[0, 1]; ax2.set_facecolor(SURFACE)
ac_op = op.groupby('Adult_Child')['Total'].sum()
wedges2, _, at2 = ax2.pie(
    ac_op.values, labels=ac_op.index, autopct='%1.1f%%', startangle=90,
    colors=[PURPLE, GOLD], wedgeprops={'edgecolor': BG, 'linewidth': 2.5},
    textprops={'color': TEXT, 'fontsize': 10})
for at in at2:
    at.set_color(BG); at.set_fontweight('bold')
centre2 = plt.Circle((0, 0), 0.55, color=SURFACE)
ax2.add_patch(centre2)
ax2.text(0, 0, 'Outpatient', ha='center', va='center', fontsize=10, color=TEXT, fontweight='bold')
ax2.set_title('Outpatient — Adult vs Child', color='white')

# 8c: Age group stacked
ax3 = axes[1, 0]; ax3.set_facecolor(SURFACE)
age_yr = combined.groupby(['Year', 'Age_Profile'])['Total'].sum().unstack().fillna(0)
x_a = np.arange(len(age_yr)); bot = np.zeros(len(age_yr))
for col, color in zip(age_yr.columns, [CYAN, RED, GOLD]):
    ax3.bar(x_a, age_yr[col].values / 1e6, bottom=bot, color=color, alpha=0.85, label=col, edgecolor='none')
    bot += age_yr[col].values / 1e6
ax3.set_xticks(x_a); ax3.set_xticklabels(age_yr.index)
ax3.set_title('Age Group Volume by Year (Stacked)', color='white')
ax3.set_ylabel('Patients (Millions)'); ax3.grid(axis='y', alpha=0.4)
ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}M'))
ax3.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)

# 8d: Children 18+ month waits
ax4 = axes[1, 1]; ax4.set_facecolor(SURFACE)
for group, color, marker in [('Child', RED, 'o'), ('Adult', CYAN, 's')]:
    lw_g = combined[(combined['Adult_Child'] == group) &
                    (combined['Time_Bands'] == '18+ Months')].groupby('Year')['Total'].sum()
    ax4.plot(lw_g.index, lw_g.values / 1e3, color=color, marker=marker,
             lw=2.5, markersize=9, label=f'{group} 18+ Months')
    ax4.fill_between(lw_g.index, lw_g.values / 1e3, alpha=0.1, color=color)
ax4.set_title('18+ Month Waits — Children vs Adults', color='white')
ax4.set_ylabel("Patients ('000)"); ax4.grid(alpha=0.4)
ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}K'))
ax4.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax4.set_xticks([2018, 2019, 2020, 2021])

plt.tight_layout()
save(fig, '08_demographics.png')

# ── Chart 9: Statistical Tests Visualisation ──────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(18, 12), facecolor=BG)
fig.suptitle('Advanced Statistical Analysis', fontsize=13, color='white')

# 9a: Violin by year
ax1 = axes[0, 0]; ax1.set_facecolor(SURFACE)
vdata = [np.log1p(combined[combined['Year'] == y]['Total'].values) for y in [2018, 2019, 2020, 2021]]
parts = ax1.violinplot(vdata, positions=range(4), showmedians=True, showextrema=True)
for pc, color in zip(parts['bodies'], [CYAN, GREEN, GOLD, RED]):
    pc.set_facecolor(color); pc.set_alpha(0.65)
parts['cmedians'].set_color('white'); parts['cmedians'].set_lw(2)
for key in ['cbars', 'cmins', 'cmaxes']:
    parts[key].set_color(MUTED)
ax1.set_xticks(range(4)); ax1.set_xticklabels([2018, 2019, 2020, 2021])
ax1.set_title(f'Distribution by Year (log scale)\nKruskal-Wallis H={kw_h:.0f}, p<0.001', color='white')
ax1.set_ylabel('log(Total + 1)'); ax1.grid(axis='y', alpha=0.4)

# 9b: Avg wait trend + spearman
ax2 = axes[0, 1]; ax2.set_facecolor(SURFACE)
ax2.plot(avg_wait.index, avg_wait.values, color=CYAN, lw=2.5, marker='D', markersize=10, zorder=4)
m, b = np.polyfit(avg_wait.index.astype(float), avg_wait.values, 1)
ax2.plot(avg_wait.index, m*avg_wait.index.astype(float)+b,
         color=RED, ls='--', lw=2, label=f'Trend slope={m:.4f}')
ax2.fill_between(avg_wait.index, avg_wait.values, alpha=0.12, color=CYAN)
ax2.set_title(f'Avg Wait Band Rank by Year\nSpearman ρ={sp_r:.3f}, p={sp_p:.3f}', color='white')
ax2.set_ylabel('Avg Wait Rank (0=0-3mo, 6=18+mo)')
ax2.set_xticks([2018, 2019, 2020, 2021])
ax2.legend(facecolor=SURFACE, edgecolor=BORDER, labelcolor=TEXT)
ax2.grid(alpha=0.4)
for yr, val in zip(avg_wait.index, avg_wait.values):
    ax2.annotate(f'{val:.3f}', (yr, val), xytext=(0, 12),
                 textcoords='offset points', ha='center', fontsize=9, color=TEXT)

# 9c: Chi-square standardised residuals
ax3 = axes[1, 0]; ax3.set_facecolor(SURFACE)
_, _, _, exp = chi2_contingency(ct_table)
resid = (ct_table.values - exp) / np.sqrt(exp)
resid_df = pd.DataFrame(resid, index=ct_table.index, columns=ct_table.columns)
cmap_div = LinearSegmentedColormap.from_list('div', [RED, SURFACE, CYAN])
sns.heatmap(resid_df, ax=ax3, cmap=cmap_div, center=0, annot=True, fmt='.2f',
            linewidths=0.5, linecolor=BG, annot_kws={'size': 9, 'color': 'white'},
            cbar_kws={'shrink': 0.8})
ax3.set_title(f"Chi-Square Standardised Residuals\nAdult/Child × Time Band | Cramér's V={cramers_v:.3f}", color='white')
ax3.tick_params(colors=MUTED, labelsize=8)
ax3.set_xticklabels(ax3.get_xticklabels(), rotation=35, ha='right')
cbar3 = ax3.collections[0].colorbar
cbar3.ax.tick_params(colors=MUTED)

# 9d: Correlation matrix
ax4 = axes[1, 1]; ax4.set_facecolor(SURFACE)
sns.heatmap(corr_num, ax=ax4, cmap=cmap_div, center=0, vmin=-1, vmax=1,
            annot=True, fmt='.3f', linewidths=0.5, linecolor=BG,
            annot_kws={'size': 12, 'color': 'white'},
            cbar_kws={'shrink': 0.8})
ax4.set_title('Pearson Correlation Matrix\n(Specialty-Year Level)', color='white')
ax4.tick_params(colors=MUTED)
cbar4 = ax4.collections[0].colorbar
cbar4.ax.tick_params(colors=MUTED)

plt.tight_layout()
save(fig, '09_statistical_analysis.png')

# ── Chart 10: Specialty Group Risk Matrix ─────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(20, 9), facecolor=BG)
fig.suptitle('Specialty Group — Volume vs Long-Wait Risk', fontsize=13, color='white', y=1.01)

for ax, (df, label) in zip(axes, [(combined[combined['Patient_Type']=='Inpatient'], 'Inpatient'),
                                   (combined[combined['Patient_Type']=='Outpatient'], 'Outpatient')]):
    ax.set_facecolor(SURFACE)
    grp = df.groupby('Specialty Group').agg(
        Total=('Total', 'sum'),
        Records=('Total', 'count')
    ).reset_index()
    lw_grp = df[df['Time_Bands'] == '18+ Months'].groupby('Specialty Group')['Total'].sum().rename('LongWait')
    grp = grp.merge(lw_grp, on='Specialty Group', how='left').fillna(0)
    grp['LW_Pct'] = (grp['LongWait'] / grp['Total'] * 100).round(1)

    sc = ax.scatter(grp['Total'] / 1e6, grp['LW_Pct'],
                     s=grp['Records'] / grp['Records'].max() * 700 + 60,
                     c=grp['LW_Pct'], cmap='RdYlGn_r', alpha=0.85,
                     edgecolors='white', linewidths=0.6, vmin=0, vmax=12, zorder=4)
    plt.colorbar(sc, ax=ax, label='18+ Month Wait %', shrink=0.75)
    for _, row in grp.iterrows():
        ax.annotate(row['Specialty Group'],
                    (row['Total'] / 1e6, row['LW_Pct']),
                    fontsize=7.5, color=TEXT, alpha=0.9,
                    xytext=(4, 3), textcoords='offset points')
    avg_lw = grp['LW_Pct'].mean()
    ax.axhline(avg_lw, color=GOLD, ls='--', lw=1.2, alpha=0.7)
    ax.text(ax.get_xlim()[1]*0.5, avg_lw + 0.2, f'Avg: {avg_lw:.1f}%', color=GOLD, fontsize=8)
    ax.set_xlabel('Total Patients (Millions)'); ax.set_ylabel('% Patients Waiting 18+ Months')
    ax.set_title(f'{label} — Volume vs Long-Wait Risk\n(bubble size = record count)', color='white')
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.1f}M'))

plt.tight_layout()
save(fig, '10_specialty_risk_matrix.png')

# =============================================================================
# SECTION 6 — EXPORT DASHBOARD DATA TO JSON
# =============================================================================
print('\n  [INFO] Exporting dashboard JSON...')

def to_py(obj):
    if isinstance(obj, (np.integer,)): return int(obj)
    if isinstance(obj, (np.floating,)): return round(float(obj), 4)
    if isinstance(obj, np.ndarray): return [to_py(x) for x in obj]
    return obj

monthly_grp = combined.groupby(['YearMonth', 'Patient_Type'])['Total'].sum().unstack().fillna(0).reset_index()
monthly_grp = monthly_grp.sort_values('YearMonth')

age_yr_grp = combined.groupby(['Year', 'Age_Profile'])['Total'].sum().unstack().fillna(0)

grp_all = combined.groupby('Specialty Group').agg(Total=('Total','sum')).reset_index()
lw_grp_all = combined[combined['Time_Bands']=='18+ Months'].groupby('Specialty Group')['Total'].sum().rename('LongWait')
grp_all = grp_all.merge(lw_grp_all, on='Specialty Group', how='left').fillna(0)
grp_all['LW_Pct'] = (grp_all['LongWait']/grp_all['Total']*100).round(1)
grp_all = grp_all.sort_values('Total', ascending=False).head(15)

dashboard_data = {
    'kpis': {
        'total_patients':    int(combined['Total'].sum()),
        'inpatient_total':   int(ip['Total'].sum()),
        'outpatient_total':  int(op['Total'].sum()),
        'long_wait':         int(combined[combined['Time_Bands']=='18+ Months']['Total'].sum()),
        'long_wait_pct':     round(float(combined[combined['Time_Bands']=='18+ Months']['Total'].sum() /
                                         combined['Total'].sum() * 100), 1),
        'specialties':       int(combined['Specialty_Name'].nunique()),
    },
    'annual': {
        'years':      [int(y) for y in [2018, 2019, 2020, 2021]],
        'inpatient':  [int(x) for x in combined[combined['Patient_Type']=='Inpatient'].groupby('Year')['Total'].sum().values],
        'outpatient': [int(x) for x in combined[combined['Patient_Type']=='Outpatient'].groupby('Year')['Total'].sum().values],
    },
    'monthly': {
        'labels':     [str(m) for m in monthly_grp['YearMonth']],
        'inpatient':  [int(x) for x in monthly_grp.get('Inpatient',  pd.Series([0]*len(monthly_grp)))],
        'outpatient': [int(x) for x in monthly_grp.get('Outpatient', pd.Series([0]*len(monthly_grp)))],
    },
    'time_bands': {
        'labels':     TIME_ORDER,
        'inpatient':  [int(ip.groupby('Time_Bands')['Total'].sum().reindex(TIME_ORDER, fill_value=0)[t]) for t in TIME_ORDER],
        'outpatient': [int(op.groupby('Time_Bands')['Total'].sum().reindex(TIME_ORDER, fill_value=0)[t]) for t in TIME_ORDER],
    },
    'top_ip':  {
        'labels': combined[combined['Patient_Type']=='Inpatient'].groupby('Specialty_Name')['Total'].sum().nlargest(10).index.tolist(),
        'values': [int(x) for x in combined[combined['Patient_Type']=='Inpatient'].groupby('Specialty_Name')['Total'].sum().nlargest(10).values],
    },
    'top_op': {
        'labels': combined[combined['Patient_Type']=='Outpatient'].groupby('Specialty_Name')['Total'].sum().nlargest(10).index.tolist(),
        'values': [int(x) for x in combined[combined['Patient_Type']=='Outpatient'].groupby('Specialty_Name')['Total'].sum().nlargest(10).values],
    },
    'age': {
        'years':  [int(y) for y in age_yr_grp.index.tolist()],
        'groups': {col: [int(v) for v in age_yr_grp[col].tolist()] for col in age_yr_grp.columns},
    },
    'adult_child': {
        'inpatient':  {k: int(v) for k, v in ip.groupby('Adult_Child')['Total'].sum().items()},
        'outpatient': {k: int(v) for k, v in op.groupby('Adult_Child')['Total'].sum().items()},
    },
    'spec_groups': {
        'labels':  grp_all['Specialty Group'].tolist(),
        'totals':  [int(x) for x in grp_all['Total'].tolist()],
        'lw_pct':  [float(x) for x in grp_all['LW_Pct'].tolist()],
    },
    'desc_stats': [
        {k: (int(v) if isinstance(v, (np.integer,)) else round(float(v), 3) if isinstance(v, float) else v)
         for k, v in stat_ip.items()},
        {k: (int(v) if isinstance(v, (np.integer,)) else round(float(v), 3) if isinstance(v, float) else v)
         for k, v in stat_op.items()},
        {k: (int(v) if isinstance(v, (np.integer,)) else round(float(v), 3) if isinstance(v, float) else v)
         for k, v in stat_all.items()},
    ],
    'stat_tests': {
        'kw_h': round(float(kw_h), 4), 'kw_p': float(kw_p),
        'mw_u': float(mw_u),           'mw_p': float(mw_p),
        'chi2': round(float(chi2_val),2), 'chi2_p': float(chi2_p),
        'cramers_v': round(float(cramers_v), 4),
        'sp_r': round(float(sp_r), 4),    'sp_p': float(sp_p),
        'pearson_r': round(float(pr), 4), 'pearson_p': float(pp),
    },
    'long_wait_trend': {
        'labels': [str(m) for m in monthly_grp['YearMonth']],
        'inpatient': [int(x) for x in
            combined[(combined['Time_Bands']=='18+ Months') & (combined['Patient_Type']=='Inpatient')]
            .groupby('YearMonth')['Total'].sum().reindex(
                pd.PeriodIndex(monthly_grp['YearMonth'], freq='M'), fill_value=0).values],
    },
    'case_type': {
        'labels': TIME_ORDER,
        'inpatient_pct': [],
        'daycase_pct':   [],
    },
}

# Case type
ct_tb = ip.groupby(['Case_Type','Time_Bands'])['Total'].sum().unstack()
ct_tb = ct_tb.reindex(columns=TIME_ORDER, fill_value=0)
ct_pct = ct_tb.div(ct_tb.sum(axis=1), axis=0) * 100
if 'Inpatient' in ct_pct.index:
    dashboard_data['case_type']['inpatient_pct'] = [round(float(x),1) for x in ct_pct.loc['Inpatient'].values]
if 'Day Case' in ct_pct.index:
    dashboard_data['case_type']['daycase_pct'] = [round(float(x),1) for x in ct_pct.loc['Day Case'].values]

with open('/home/claude/dashboard_data.json', 'w') as f:
    json.dump(dashboard_data, f, indent=2)
print('  [SAVED] dashboard_data.json')

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print('\n' + '='*65)
print('  ANALYSIS COMPLETE — SUMMARY')
print('='*65)
print(f"""
  Total patient-waits    : {combined['Total'].sum():,}
  Inpatient              : {ip['Total'].sum():,}
  Outpatient             : {op['Total'].sum():,}
  18+ Month waiters      : {combined[combined['Time_Bands']=='18+ Months']['Total'].sum():,}
  Long-wait %            : {combined[combined['Time_Bands']=='18+ Months']['Total'].sum()/combined['Total'].sum()*100:.1f}%

  Top Inpatient specialty: {ip.groupby('Specialty_Name')['Total'].sum().idxmax()}
  Top Outpatient specialty: {op.groupby('Specialty_Name')['Total'].sum().idxmax()}

  Kruskal-Wallis (Year effect): H={kw_h:.1f}, p={kw_p:.2e}
  Mann-Whitney (IP vs OP):      p={mw_p:.2e}
  Spearman (Wait trend):        r={sp_r:.3f}, p={sp_p:.3f}
  Chi-Square Cramér V:          {cramers_v:.3f}

  Charts saved: 10 PNG files
""")
