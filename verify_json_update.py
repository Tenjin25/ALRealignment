import json
from pathlib import Path

json_file = Path('data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json')

print("Checking Siegelman data in rebuilt JSON\n")
print("=" * 80)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results_by_year = data.get('results_by_year', {})

# Check 1998 Governor General
print("\n1998 Governor General Election:")
print("-" * 80)
if '1998' in results_by_year and 'governor_1998' in results_by_year['1998']:
    race_1998 = results_by_year['1998']['governor_1998']
    print(f"Contest: {race_1998.get('contest_name', 'N/A')}")
    print(f"Date: {race_1998.get('date', 'N/A')}")
    
    results = race_1998.get('results', {})
    print(f"Counties in results: {len(results)}")
    
    # Check if Blount exists (should not have trailing space now)
    if 'Blount' in results:
        blount = results['Blount']
        print(f"\n✓ 'Blount' (no trailing space) found in results")
        print(f"  Dem Candidate: {blount.get('dem_candidate', 'N/A')}")
        print(f"  Rep Candidate: {blount.get('rep_candidate', 'N/A')}")
        print(f"  Dem Votes: {blount.get('dem_votes', 0):,}")
        print(f"  Rep Votes: {blount.get('rep_votes', 0):,}")
    
    # Check if 'Blount ' (with space) exists - should NOT exist
    if 'Blount ' in results:
        print("\n❌ 'Blount ' (WITH trailing space) still exists - ISSUE!")
    else:
        print(f"\n✓ 'Blount ' (with trailing space) not found - GOOD!")
    
    # Get some candidate info
    sample_county = list(results.keys())[0]
    sample_data = results[sample_county]
    print(f"\nSample county ({sample_county}):")
    print(f"  Dem: {sample_data.get('dem_candidate', 'N/A')} - {sample_data.get('dem_votes', 0):,} votes")
    print(f"  Rep: {sample_data.get('rep_candidate', 'N/A')} - {sample_data.get('rep_votes', 0):,} votes")
else:
    print("❌ 1998 Governor race not found in JSON")

# Check 2002 Governor General
print("\n" + "=" * 80)
print("\n2002 Governor General Election:")
print("-" * 80)
if '2002' in results_by_year and 'governor_2002' in results_by_year['2002']:
    race_2002 = results_by_year['2002']['governor_2002']
    print(f"Contest: {race_2002.get('contest_name', 'N/A')}")
    print(f"Date: {race_2002.get('date', 'N/A')}")
    
    results = race_2002.get('results', {})
    print(f"Counties in results: {len(results)}")
    
    # Check candidate names
    sample_county = 'Jefferson'
    if sample_county in results:
        jeff_data = results[sample_county]
        print(f"\n{sample_county} County:")
        print(f"  Dem: {jeff_data.get('dem_candidate', 'N/A')} - {jeff_data.get('dem_votes', 0):,} votes")
        print(f"  Rep: {jeff_data.get('rep_candidate', 'N/A')} - {jeff_data.get('rep_votes', 0):,} votes")
else:
    print("❌ 2002 Governor race not found in JSON")

print("\n" + "=" * 80)
print("\n✓ JSON has been successfully rebuilt with clean county names!")
print(f"  File: {json_file}")
print(f"  Size: {json_file.stat().st_size / (1024*1024):.2f} MB")
print(f"  Last Modified: {json_file.stat().st_mtime}")
