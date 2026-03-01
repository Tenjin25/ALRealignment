import pandas as pd
from pathlib import Path
import sys

# Fix encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data_dir = Path('data')

# Get all governor CSV files (excluding openelections directories which are clean)
governor_files = []
for pattern in ['eagovernor*.csv', 'ealtgovernor*.csv', 'eaattorneygeneral*.csv', 
                'eaauditor*.csv', 'eatreasurer*.csv', 'eacommissionerag*.csv',
                'eaussenate*.csv', 'eapresidentgeneral*.csv']:
    governor_files.extend(data_dir.glob(pattern))

print(f'Found {len(governor_files)} CSV files to fix\n')
print('=' * 80)

fixed_count = 0
files_with_issues = []

for csv_file in sorted(governor_files):
    try:
        df = pd.read_csv(csv_file, dtype=str).fillna('')
        
        # Find the county column
        county_col = None
        for col in df.columns:
            if 'county' in col.lower() or col.strip().lower() == 'county':
                county_col = col
                break
        
        if not county_col:
            continue
        
        # Check for trailing or leading spaces
        has_trailing = df[county_col].str.endswith(' ')
        has_leading = df[county_col].str.startswith(' ')
        
        if has_trailing.any() or has_leading.any():
            print(f'\n{csv_file.name}')
            
            # Strip spaces from county column
            original_values = df[county_col].copy()
            df[county_col] = df[county_col].str.strip()
            
            # Count changes
            changed = (original_values != df[county_col]).sum()
            print(f'  Fixed {changed} county names with trailing/leading spaces')
            
            # Save the fixed file
            df.to_csv(csv_file, index=False)
            fixed_count += 1
            files_with_issues.append(csv_file.name)
            
    except Exception as e:
        print(f'\n{csv_file.name}')
        print(f'  [ERROR] {e}')

print('\n' + '=' * 80)
print(f'\nSUMMARY:')
print(f'  Fixed {fixed_count} files')

if files_with_issues:
    print(f'\n  Files that were fixed:')
    for filename in files_with_issues:
        print(f'    - {filename}')
else:
    print('  No files needed fixing!')
