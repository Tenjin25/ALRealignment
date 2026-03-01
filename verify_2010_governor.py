import json
from pathlib import Path

json_file = Path('data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json')

print("2010 Governor Race Details\n")
print("=" * 80)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

results_by_year = data.get('results_by_year', {})

if '2010' in results_by_year and 'governor_2010' in results_by_year['2010']:
    race_2010 = results_by_year['2010']['governor_2010']
    
    print(f"Contest: {race_2010.get('contest_name', 'N/A')}")
    print(f"Date: {race_2010.get('date', 'N/A')}")
    print(f"State: {race_2010.get('state', 'N/A')}")
    
    results = race_2010.get('results', {})
    print(f"Counties: {len(results)}")
    
    # Get sample data
    sample_counties = ['Jefferson', 'Mobile', 'Madison', 'Autauga']
    print("\nSample Counties:")
    print("-" * 80)
    for county in sample_counties:
        if county in results:
            data = results[county]
            print(f"\n{county}:")
            print(f"  Dem: {data.get('dem_candidate', 'N/A')} - {data.get('dem_votes', 0):,} votes")
            print(f"  Rep: {data.get('rep_candidate', 'N/A')} - {data.get('rep_votes', 0):,} votes")
            print(f"  Winner: {data.get('winner', 'N/A')} ({data.get('winner_party', 'N/A')})")
            print(f"  Margin: {data.get('margin_pct', 'N/A')}")
    
    # Calculate statewide totals
    total_dem = sum(r.get('dem_votes', 0) for r in results.values())
    total_rep = sum(r.get('rep_votes', 0) for r in results.values())
    total_votes = sum(r.get('total_votes', 0) for r in results.values())
    
    print("\n" + "=" * 80)
    print("\nStatewide Totals (2010 Governor):")
    print("-" * 80)
    print(f"Ron Sparks (DEM): {total_dem:,} votes ({total_dem/total_votes*100:.2f}%)")
    print(f"Robert Bentley (REP): {total_rep:,} votes ({total_rep/total_votes*100:.2f}%)")
    print(f"Margin: {total_rep - total_dem:,} votes (Bentley +{(total_rep-total_dem)/total_votes*100:.2f}%)")
    print(f"Total Votes: {total_votes:,}")
    
    print("\n✓ 2010 Governor race successfully added to JSON!")
else:
    print("❌ 2010 Governor race still not found")
