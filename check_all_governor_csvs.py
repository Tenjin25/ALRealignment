import pandas as pd
from pathlib import Path
import sys

# Fix encoding for Windows console
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data_dir = Path('data')
governor_files = sorted(data_dir.glob('eagovernor*.csv'))

print(f'Found {len(governor_files)} governor CSV files\n')
print('=' * 100)

issues_found = []

for csv_file in governor_files:
    print(f'\n{csv_file.name}')
    print('-' * 100)
    
    try:
        df = pd.read_csv(csv_file, dtype=str).fillna('')
        
        # Find the county column
        county_col = None
        for col in df.columns:
            if 'county' in col.lower() or col.strip().lower() == 'county':
                county_col = col
                break
        
        if not county_col:
            print('  [ERROR] No County column found')
            issues_found.append((csv_file.name, 'No County column'))
            continue
        
        # Check for unnamed columns
        unnamed_cols = [col for col in df.columns if 'unnamed' in col.lower()]
        if unnamed_cols:
            print(f'  [WARN] Unnamed columns: {len(unnamed_cols)} columns')
            issues_found.append((csv_file.name, f'{len(unnamed_cols)} unnamed columns'))
        
        # Get county data (exclude aggregate rows)
        exclude_keywords = ['calculated', 'reported', 'total', 'totals', 'margin', 'unnamed', '']
        county_data = df[~df[county_col].str.strip().str.lower().isin(exclude_keywords)]
        
        # Check for trailing spaces
        has_trailing = county_data[county_col].str.endswith(' ')
        if has_trailing.any():
            counties_with_spaces = county_data[has_trailing][county_col].tolist()
            print(f'  [WARN] Counties with trailing spaces: {len(counties_with_spaces)}')
            for county in counties_with_spaces[:5]:  # Show first 5
                print(f'      "{county}"')
            if len(counties_with_spaces) > 5:
                print(f'      ... and {len(counties_with_spaces) - 5} more')
            issues_found.append((csv_file.name, f'{len(counties_with_spaces)} trailing spaces'))
        
        # Check for leading spaces
        has_leading = county_data[county_col].str.startswith(' ')
        if has_leading.any():
            counties_with_spaces = county_data[has_leading][county_col].tolist()
            print(f'  [WARN] Counties with leading spaces: {len(counties_with_spaces)}')
            issues_found.append((csv_file.name, f'{len(counties_with_spaces)} leading spaces'))
        
        # Check for duplicates
        duplicates = county_data[county_col].duplicated()
        if duplicates.any():
            dup_counties = county_data[duplicates][county_col].tolist()
            print(f'  [WARN] Duplicate counties: {len(dup_counties)}')
            for county in dup_counties[:5]:
                print(f'      {county}')
            issues_found.append((csv_file.name, f'{len(dup_counties)} duplicates'))
        
        # Check county count
        county_count = len(county_data)
        if county_count != 67:
            print(f'  [WARN] County count: {county_count} (expected 67)')
            issues_found.append((csv_file.name, f'County count: {county_count}'))
        
        # Check for aggregate rows
        agg_rows = df[df[county_col].str.strip().str.lower().isin(['calculated', 'reported', 'total', 'totals', 'margin'])]
        if len(agg_rows) > 0:
            print(f'  [INFO] Aggregate rows: {len(agg_rows)} (', ', '.join(agg_rows[county_col].tolist()), ')')
            
            # Try to verify aggregation for numeric columns
            numeric_cols = [col for col in df.columns if col != county_col and 'unnamed' not in col.lower()]
            if numeric_cols and len(agg_rows) > 0:
                # Check first aggregate row
                agg_row = agg_rows.iloc[0]
                agg_name = agg_row[county_col].strip()
                
                for col in numeric_cols[:3]:  # Check first 3 columns
                    try:
                        county_sum = pd.to_numeric(county_data[col], errors='coerce').fillna(0).sum()
                        agg_value = pd.to_numeric(agg_row[col], errors='coerce')
                        if pd.notna(agg_value) and abs(county_sum - agg_value) > 0.01:
                            print(f'  [ERROR] Aggregation mismatch in "{col}": counties={county_sum:.0f}, {agg_name}={agg_value:.0f}, diff={county_sum - agg_value:.0f}')
                            issues_found.append((csv_file.name, f'Aggregation mismatch in {col}'))
                    except:
                        pass
        
        # If no issues found for this file
        if csv_file.name not in [issue[0] for issue in issues_found]:
            print('  [OK] No issues found')
    
    except Exception as e:
        print(f'  [ERROR] Error reading file: {e}')
        issues_found.append((csv_file.name, f'Error: {e}'))

print('\n' + '=' * 100)
print(f'\nSUMMARY: Found issues in {len(set([i[0] for i in issues_found]))} files')

if issues_found:
    print('\nFiles with issues:')
    current_file = None
    for filename, issue in issues_found:
        if filename != current_file:
            print(f'\n  {filename}')
            current_file = filename
        print(f'    - {issue}')
