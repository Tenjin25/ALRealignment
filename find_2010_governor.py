import json
from pathlib import Path

json_file = Path('data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json')

print("Searching for 2010 Governor race\n")
print("=" * 80)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results_by_year = data.get('results_by_year', {})

# Check what's in 2010
print("\nYear 2010 contests:")
print("-" * 80)
if '2010' in results_by_year:
    contests_2010 = results_by_year['2010']
    print(f"Found {len(contests_2010)} contests in 2010:")
    for contest_key, contest_data in sorted(contests_2010.items()):
        contest_name = contest_data.get('contest_name', contest_key)
        date = contest_data.get('date', 'N/A')
        num_counties = len(contest_data.get('results', {}))
        print(f"  - {contest_key:40s} {contest_name:30s} ({num_counties} counties, date: {date})")
else:
    print("❌ Year 2010 not found in JSON")

# Check all years for governor races
print("\n" + "=" * 80)
print("\nAll Governor races in JSON:")
print("-" * 80)

governor_years = []
for year in sorted(results_by_year.keys()):
    for contest_key in results_by_year[year].keys():
        if 'governor' in contest_key.lower() and contest_key.startswith('governor_'):
            governor_years.append(year)
            contest_data = results_by_year[year][contest_key]
            contest_name = contest_data.get('contest_name', contest_key)
            date = contest_data.get('date', 'N/A')
            print(f"  {year}: {contest_key:30s} ({contest_name}, {date})")

print(f"\nTotal Governor races: {len(governor_years)}")
print(f"Years with Governor: {', '.join(governor_years)}")

# Check if the data exists in the source directory
print("\n" + "=" * 80)
print("\nChecking source data for 2010 Governor:")
print("-" * 80)

source_dir = Path('data/openelections_office_normalized')
gov_2010_files = list(source_dir.glob('*2010*governor*.csv'))

if gov_2010_files:
    print(f"Found {len(gov_2010_files)} 2010 governor files:")
    for f in gov_2010_files:
        print(f"  - {f.name}")
else:
    print("❌ No 2010 governor files found in openelections_office_normalized")

# Also check the main data directory
data_dir = Path('data')
gov_2010_legacy = list(data_dir.glob('*governor*2010*.csv')) + list(data_dir.glob('*governor*Gen10*.csv'))

if gov_2010_legacy:
    print(f"\nFound {len(gov_2010_legacy)} 2010 governor files in data/:")
    for f in gov_2010_legacy:
        print(f"  - {f.name}")

print("\n" + "=" * 80)
