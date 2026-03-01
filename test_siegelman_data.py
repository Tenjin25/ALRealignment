import pandas as pd
from pathlib import Path

print("Testing Siegelman Data Loading\n")
print("=" * 80)

# Test 1998 General Election (Siegelman won)
file_1998 = Path('data/openelections_office_normalized/19981103__al__general__county__governor.csv')
print(f"\n1. 1998 General Election: {file_1998.name}")
print("-" * 80)

df_1998 = pd.read_csv(file_1998)
print(f"Total rows: {len(df_1998)}")
print(f"Columns: {list(df_1998.columns)}")
print()

# Get statewide totals
siegelman_votes = df_1998[df_1998['candidate'] == 'Don Siegelman']['votes'].astype(int).sum()
james_votes = df_1998[df_1998['candidate'] == 'Fob James']['votes'].astype(int).sum()
total_votes = siegelman_votes + james_votes

print(f"Don Siegelman (DEM): {siegelman_votes:,} votes ({siegelman_votes/total_votes*100:.2f}%)")
print(f"Fob James (REP): {james_votes:,} votes ({james_votes/total_votes*100:.2f}%)")
print(f"Margin: {siegelman_votes - james_votes:,} votes")
print()

# Show sample counties
print("Sample counties:")
sample = df_1998[df_1998['candidate'].isin(['Don Siegelman', 'Fob James'])].head(10)
print(sample[['county', 'party', 'candidate', 'votes']].to_string(index=False))

# Test 2002 General Election (Siegelman lost)
print("\n" + "=" * 80)
file_2002 = Path('data/openelections_office_normalized/20021105__al__general__county__governor.csv')
print(f"\n2. 2002 General Election: {file_2002.name}")
print("-" * 80)

df_2002 = pd.read_csv(file_2002)
print(f"Total rows: {len(df_2002)}")
print(f"Columns: {list(df_2002.columns)}")
print()

# Get statewide totals (note: different name format)
siegelman_votes = df_2002[df_2002['candidate'] == 'Siegelman, Don']['votes'].astype(int).sum()
riley_votes = df_2002[df_2002['candidate'] == 'Riley, Bob']['votes'].astype(int).sum()
total_votes = siegelman_votes + riley_votes

print(f"Don Siegelman (DEM): {siegelman_votes:,} votes ({siegelman_votes/total_votes*100:.2f}%)")
print(f"Bob Riley (REP): {riley_votes:,} votes ({riley_votes/total_votes*100:.2f}%)")
print(f"Margin: {riley_votes - siegelman_votes:,} votes (Riley won)")
print()

# Check for any data quality issues
print("\nData Quality Checks:")
print("-" * 80)
counties_1998 = df_1998['county'].unique()
counties_2002 = df_2002['county'].unique()
print(f"1998 Counties: {len(counties_1998)} (should be 67)")
print(f"2002 Counties: {len(counties_2002)} (includes Total rows, should be 67 + some totals)")
print()

# Check for trailing spaces
has_trailing_1998 = df_1998['county'].str.endswith(' ').any()
has_trailing_2002 = df_2002['county'].str.endswith(' ').any()
print(f"1998 Trailing spaces: {'YES - ISSUE!' if has_trailing_1998 else 'No - Clean ✓'}")
print(f"2002 Trailing spaces: {'YES - ISSUE!' if has_trailing_2002 else 'No - Clean ✓'}")

print("\n" + "=" * 80)
print("\n✓ Siegelman data loads successfully from openelections_office_normalized files!")
