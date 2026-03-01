import json
from pathlib import Path
from collections import Counter

json_file = Path('data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json')

print("Analyzing all contests in JSON\n")
print("=" * 80)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results_by_year = data.get('results_by_year', {})

# Get all contest types
all_contests = []
year_contest_map = {}

for year, contests in sorted(results_by_year.items()):
    year_contests = []
    for contest_key, contest_data in contests.items():
        contest_name = contest_data.get('contest_name', contest_key)
        year_contests.append((contest_key, contest_name))
        all_contests.append(contest_key.split('_')[0])  # Get office type
    year_contest_map[year] = year_contests

# Count contest types
contest_counts = Counter(all_contests)

print("\nContest Types Found:")
print("-" * 80)
for contest_type, count in sorted(contest_counts.items()):
    print(f"  {contest_type:30s}: {count:3d} races")

print(f"\n  Total Races: {sum(contest_counts.values())}")

# Sample years to check
sample_years = ['1986', '1998', '2002', '2010']

print("\n" + "=" * 80)
print("\nSample Years - Contests Available:")
print("-" * 80)

for year in sample_years:
    if year in year_contest_map:
        print(f"\n{year}:")
        for contest_key, contest_name in year_contest_map[year]:
            print(f"  - {contest_key:40s} ({contest_name})")

# Check for trailing spaces across all contests
print("\n" + "=" * 80)
print("\nData Quality Check Across All Contests:")
print("-" * 80)

issues_found = []
total_counties_checked = 0
contests_checked = 0

for year, contests in results_by_year.items():
    for contest_key, contest_data in contests.items():
        contests_checked += 1
        results = contest_data.get('results', {})
        
        for county_name in results.keys():
            total_counties_checked += 1
            # Check for trailing or leading spaces
            if county_name != county_name.strip():
                issues_found.append((year, contest_key, county_name))

if issues_found:
    print(f"❌ Found {len(issues_found)} counties with space issues:")
    for year, contest, county in issues_found[:10]:  # Show first 10
        print(f"  {year} - {contest} - '{county}'")
    if len(issues_found) > 10:
        print(f"  ... and {len(issues_found) - 10} more")
else:
    print(f"✓ All {total_counties_checked:,} county entries are clean (no trailing/leading spaces)")
    print(f"  Checked {contests_checked} contests across {len(results_by_year)} years")

# Check specific contest types for Blount
print("\n" + "=" * 80)
print("\nChecking 'Blount' (no space) vs 'Blount ' (with space):")
print("-" * 80)

blount_clean_count = 0
blount_space_count = 0

for year, contests in results_by_year.items():
    for contest_key, contest_data in contests.items():
        results = contest_data.get('results', {})
        if 'Blount' in results:
            blount_clean_count += 1
        if 'Blount ' in results:
            blount_space_count += 1

print(f"  'Blount' (clean): {blount_clean_count} occurrences")
print(f"  'Blount ' (with space): {blount_space_count} occurrences")

if blount_space_count == 0:
    print("\n✓ No trailing spaces found in any contest!")
else:
    print(f"\n❌ Still have trailing space issues in {blount_space_count} contests")

print("\n" + "=" * 80)
print("\n✓ JSON verification complete!")
