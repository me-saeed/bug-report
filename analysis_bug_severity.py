#!/usr/bin/env python3
"""
Evidence-Based Software Engineering Analysis:
Factors Associated with Bug Severity in Software Projects

This script performs data inspection, cleaning, analysis, and visualization
on a Kaggle bug-report dataset.
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Create figures directory
figures_dir = Path('figures')
figures_dir.mkdir(exist_ok=True)

print("=" * 60)
print("STEP 1: Locate & Observe the Dataset")
print("=" * 60)

# Load dataset
dataset_file = 'issues.csv'
print(f"\nLoading dataset: {dataset_file}")

# For large files, we'll use chunking to get statistics
# Sample a manageable subset for analysis
print("\nReading dataset in chunks and sampling...")
chunk_size = 10000
chunks = []
target_rows = 100000  # Sample 100K rows for analysis

# Read a manageable sample directly
print("  Reading sample of dataset...")
df = pd.read_csv(dataset_file, nrows=target_rows, low_memory=False)
print(f"Loaded {len(df):,} rows for analysis (sampling from larger dataset)")

print(f"\nDataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"\nColumn names:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i:2d}. {col}")

print("\n" + "=" * 60)
print("Data Sample (first 5 rows):")
print("=" * 60)
print(df.head())

print("\n" + "=" * 60)
print("Missing Values Summary:")
print("=" * 60)
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_df = pd.DataFrame({
    'Missing Count': missing,
    'Missing %': missing_pct
})
print(missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False))

# Identify key columns
print("\n" + "=" * 60)
print("Identifying Key Columns:")
print("=" * 60)

# Priority appears to be our severity field
if 'priority.name' in df.columns:
    print(f"\nSeverity field: priority.name")
    print(f"Unique values: {df['priority.name'].value_counts()}")
    
if 'priority.id' in df.columns:
    print(f"\nPriority IDs: {df['priority.id'].value_counts()}")

if 'status.name' in df.columns:
    print(f"\nStatus field: status.name")
    print(f"Unique values: {df['status.name'].value_counts().head(10)}")

if 'project.name' in df.columns:
    print(f"\nProject field: project.name")
    print(f"Top projects: {df['project.name'].value_counts().head(10)}")

if 'issuetype.name' in df.columns:
    print(f"\nIssue Type field: issuetype.name")
    print(f"Unique values: {df['issuetype.name'].value_counts()}")

print("\n" + "=" * 60)
print("STEP 2: Clean & Prepare the Data")
print("=" * 60)

# Create a copy for cleaning
df_clean = df.copy()

# Remove rows where priority (severity) is missing
initial_count = len(df_clean)
print(f"\nInitial row count: {initial_count:,}")

df_clean = df_clean.dropna(subset=['priority.name'])
print(f"After removing missing priority: {len(df_clean):,} rows ({initial_count - len(df_clean):,} removed)")

# Standardize severity labels (trim whitespace, consistent casing)
df_clean['priority.name'] = df_clean['priority.name'].str.strip()
df_clean['priority.name'] = df_clean['priority.name'].str.title()

print(f"\nSeverity distribution after standardization:")
print(df_clean['priority.name'].value_counts().sort_index())

# Check if we need to map to smaller set
unique_severities = df_clean['priority.name'].nunique()
print(f"\nNumber of unique severity levels: {unique_severities}")

# The dataset already has a good set: Blocker, Critical, Major, Minor, Trivial
# We'll keep them as is, but ensure consistent naming
severity_mapping = {
    'Blocker': 'Blocker',
    'Critical': 'Critical',
    'Major': 'Major',
    'Minor': 'Minor',
    'Trivial': 'Trivial'
}

# Filter to only known severities
df_clean = df_clean[df_clean['priority.name'].isin(severity_mapping.keys())]
print(f"After filtering to known severities: {len(df_clean):,} rows")

# Select relevant columns for analysis
analysis_cols = ['priority.name', 'status.name', 'project.name', 'issuetype.name']
if 'summary' in df_clean.columns:
    analysis_cols.append('summary')
if 'description' in df_clean.columns:
    analysis_cols.append('description')

df_analysis = df_clean[analysis_cols].copy()
df_analysis = df_analysis.rename(columns={'priority.name': 'severity'})

# Create derived fields
print("\nCreating derived fields...")

# Description length (character count)
if 'description' in df_analysis.columns:
    df_analysis['desc_length'] = df_analysis['description'].fillna('').str.len()
    print(f"Created desc_length: mean={df_analysis['desc_length'].mean():.1f}, median={df_analysis['desc_length'].median():.1f}")
elif 'summary' in df_analysis.columns:
    df_analysis['desc_length'] = df_analysis['summary'].fillna('').str.len()
    print(f"Created desc_length from summary: mean={df_analysis['desc_length'].mean():.1f}, median={df_analysis['desc_length'].median():.1f}")

# Top components/projects grouping
if 'project.name' in df_analysis.columns:
    top_projects = df_analysis['project.name'].value_counts().head(10).index.tolist()
    df_analysis['project_grouped'] = df_analysis['project.name'].apply(
        lambda x: x if pd.notna(x) and x in top_projects else 'Other'
    )
    print(f"Created project_grouped: top 10 projects + 'Other'")

# Clean status
if 'status.name' in df_analysis.columns:
    df_analysis['status.name'] = df_analysis['status.name'].fillna('Unknown')

# Clean issue type
if 'issuetype.name' in df_analysis.columns:
    df_analysis['issuetype.name'] = df_analysis['issuetype.name'].fillna('Unknown')

print(f"\nFinal cleaned dataset: {len(df_analysis):,} rows × {len(df_analysis.columns)} columns")

print("\n" + "=" * 60)
print("STEP 3: Analysis (Create Evidence)")
print("=" * 60)

# 1. Severity distribution
print("\n1. Severity Distribution:")
severity_dist = df_analysis['severity'].value_counts().sort_index()
severity_pct = (df_analysis['severity'].value_counts(normalize=True) * 100).sort_index()
severity_summary = pd.DataFrame({
    'Count': severity_dist,
    'Percentage': severity_pct.round(2)
})
print(severity_summary)

# 2. Severity vs Priority (actually Severity vs Status)
print("\n2. Severity vs Status (Cross-tabulation):")
if 'status.name' in df_analysis.columns:
    severity_status = pd.crosstab(df_analysis['severity'], df_analysis['status.name'], margins=True)
    print(severity_status)

# 3. Severity vs Component/Project
print("\n3. Severity vs Project (Top Projects):")
if 'project_grouped' in df_analysis.columns:
    severity_project = pd.crosstab(df_analysis['severity'], df_analysis['project_grouped'])
    print(severity_project)

# 4. Severity vs Issue Type
print("\n4. Severity vs Issue Type:")
if 'issuetype.name' in df_analysis.columns:
    severity_issuetype = pd.crosstab(df_analysis['severity'], df_analysis['issuetype.name'])
    print(severity_issuetype)

# 5. Text analysis - Description length by severity
print("\n5. Description Length by Severity:")
if 'desc_length' in df_analysis.columns:
    desc_by_severity = df_analysis.groupby('severity')['desc_length'].agg(['count', 'mean', 'median', 'std'])
    print(desc_by_severity.round(2))

print("\n" + "=" * 60)
print("STEP 4: Generate Graphs")
print("=" * 60)

# Set style
plt.style.use('default')

# 1. Severity distribution bar chart
print("\nGenerating Figure 1: severity_distribution.png")
fig, ax = plt.subplots(figsize=(10, 6))
severity_order = ['Blocker', 'Critical', 'Major', 'Minor', 'Trivial']
severity_counts = df_analysis['severity'].value_counts().reindex(severity_order, fill_value=0)
bars = ax.bar(severity_counts.index, severity_counts.values)
ax.set_xlabel('Severity Level', fontsize=12)
ax.set_ylabel('Number of Issues', fontsize=12)
ax.set_title('Distribution of Bug Severity Levels', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height):,}',
            ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('figures/severity_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: figures/severity_distribution.png")

# 2. Severity vs Status
print("\nGenerating Figure 2: severity_vs_status.png")
if 'status.name' in df_analysis.columns:
    fig, ax = plt.subplots(figsize=(12, 7))
    severity_status_plot = pd.crosstab(df_analysis['severity'], df_analysis['status.name'])
    # Get top 5 statuses by frequency
    top_statuses = df_analysis['status.name'].value_counts().head(5).index
    severity_status_plot = severity_status_plot[top_statuses]
    severity_status_plot = severity_status_plot.reindex(severity_order, fill_value=0)
    
    severity_status_plot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_xlabel('Severity Level', fontsize=12)
    ax.set_ylabel('Number of Issues', fontsize=12)
    ax.set_title('Severity Distribution by Status (Top 5 Statuses)', fontsize=14, fontweight='bold')
    ax.legend(title='Status', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('figures/severity_vs_status.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: figures/severity_vs_status.png")

# 3. Severity vs Project (Top Components)
print("\nGenerating Figure 3: severity_vs_component_top.png")
if 'project_grouped' in df_analysis.columns:
    fig, ax = plt.subplots(figsize=(12, 7))
    severity_project_plot = pd.crosstab(df_analysis['severity'], df_analysis['project_grouped'])
    severity_project_plot = severity_project_plot.reindex(severity_order, fill_value=0)
    
    # Sort columns by total (excluding 'Other' if it's too large)
    col_order = severity_project_plot.sum().sort_values(ascending=False).index.tolist()
    if 'Other' in col_order:
        col_order.remove('Other')
        col_order.append('Other')
    severity_project_plot = severity_project_plot[col_order]
    
    severity_project_plot.plot(kind='bar', ax=ax, width=0.8)
    ax.set_xlabel('Severity Level', fontsize=12)
    ax.set_ylabel('Number of Issues', fontsize=12)
    ax.set_title('Severity Distribution by Project (Top 10 Projects)', fontsize=14, fontweight='bold')
    ax.legend(title='Project', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('figures/severity_vs_component_top.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: figures/severity_vs_component_top.png")

# 4. Description length by severity (boxplot)
print("\nGenerating Figure 4: desc_length_by_severity.png")
if 'desc_length' in df_analysis.columns:
    fig, ax = plt.subplots(figsize=(10, 6))
    data_for_box = [df_analysis[df_analysis['severity'] == sev]['desc_length'].values 
                     for sev in severity_order if sev in df_analysis['severity'].values]
    labels_for_box = [sev for sev in severity_order if sev in df_analysis['severity'].values]
    
    bp = ax.boxplot(data_for_box, labels=labels_for_box, patch_artist=True)
    ax.set_xlabel('Severity Level', fontsize=12)
    ax.set_ylabel('Description Length (characters)', fontsize=12)
    ax.set_title('Description Length Distribution by Severity Level', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig('figures/desc_length_by_severity.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: figures/desc_length_by_severity.png")

print("\n" + "=" * 60)
print("Analysis Complete!")
print("=" * 60)
print(f"\nSummary Statistics:")
print(f"  - Total issues analyzed: {len(df_analysis):,}")
print(f"  - Severity levels: {df_analysis['severity'].nunique()}")
print(f"  - Unique projects: {df_analysis['project.name'].nunique() if 'project.name' in df_analysis.columns else 'N/A'}")
print(f"\nFigures saved to: figures/")
print("\nNext step: Generate report_part2_create_evidence.md")
