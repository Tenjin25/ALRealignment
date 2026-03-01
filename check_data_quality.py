import pandas as pd

df = pd.read_csv(r'data\eagovernor1946-2010-RepPri_90.csv')

print('=== Data Quality Check ===\n')

# Check for duplicates
print('1. Checking for duplicate counties:')
exclude = ['Calculated', 'Reported', 'Total', 'totals', 'Margin']
county_data = df[~df['County'].str.strip().isin(exclude)]
duplicates = county_data['County'].duplicated()
if duplicates.any():
    print('  Found duplicates:')
    print(county_data[duplicates][['County']])
else:
    print('  No duplicate counties found')
print()

# Check for trailing spaces
print('2. Checking for trailing spaces in county names:')
has_trailing = county_data['County'].str.endswith(' ')
if has_trailing.any():
    print('  Counties with trailing spaces:')
    for idx, row in county_data[has_trailing].iterrows():
        print(f'    "{row["County"]}" (row {idx})')
else:
    print('  No trailing spaces found')
print()

# Check for missing values
print('3. Checking for missing values:')
cols = ['Guy Hunt', 'Jack Pollard', 'Jim Watley']
for col in cols:
    missing = county_data[col].isna().sum()
    if missing > 0:
        print(f'  {col}: {missing} missing values')
if county_data[cols].isna().sum().sum() == 0:
    print('  No missing values found')
print()

# Show Alabama county count
print(f'4. County count: {len(county_data)} (Alabama has 67 counties)')
print()

# Show all rows for inspection
print('5. All data rows:')
print(df.to_string())
