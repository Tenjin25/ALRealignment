import pandas as pd

df = pd.read_csv(r'data\eagovernor1946-2010-RepPri_90.csv')
print('Total rows:', len(df))
print()

exclude = ['Calculated', 'Reported', 'Total', 'totals', 'Margin']
county_data = df[~df['County'].str.strip().isin(exclude)]
print('County rows:', len(county_data))
print()

cols = ['Guy Hunt', 'Jack Pollard', 'Jim Watley']
sums = {col: county_data[col].sum() for col in cols}
print('Actual county sums:')
for col, val in sums.items():
    print(f'  {col}: {val}')
print()

print('Reported Calculated row:')
calc_row = df[df['County'].str.strip() == 'Calculated']
if not calc_row.empty:
    for col in cols:
        print(f'  {col}: {calc_row[col].values[0]}')
else:
    print('  No Calculated row found')
print()

if not calc_row.empty:
    match = all(sums[col] == calc_row[col].values[0] for col in cols)
    print('Match?', match)
    if not match:
        print('\nDiscrepancies:')
        for col in cols:
            if sums[col] != calc_row[col].values[0]:
                print(f'  {col}: calculated={sums[col]}, reported={calc_row[col].values[0]}, diff={sums[col]-calc_row[col].values[0]}')
