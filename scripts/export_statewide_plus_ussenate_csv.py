import csv
import json
from pathlib import Path


INPUT_JSON = Path("results_by_year_grouped.statewide_plus_ussenate_1968_2026.json")
OUTPUT_DIR = Path("data/csv_exports")


COUNTY_ROWS_CSV = OUTPUT_DIR / "contest_county_results.csv"
CANDIDATE_ROWS_CSV = OUTPUT_DIR / "candidate_results.csv"
SUMMARY_ROWS_CSV = OUTPUT_DIR / "contest_year_statewide_summary.csv"


def to_int(value):
    try:
        return int(value)
    except Exception:
        return 0


def main() -> None:
    payload = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    results_by_year = payload.get("results_by_year", {})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    county_fieldnames = [
        "year",
        "contest_key",
        "contest_name",
        "date",
        "state",
        "county",
        "dem_candidate",
        "rep_candidate",
        "dem_votes",
        "rep_votes",
        "other_votes",
        "total_votes",
        "two_party_total",
        "margin",
        "margin_pct",
        "winner",
        "winner_name",
        "winner_party",
        "winner_votes",
        "winner_incumbent",
        "competitiveness_category",
        "competitiveness_party",
        "competitiveness_code",
        "competitiveness_color",
    ]

    candidate_fieldnames = [
        "year",
        "contest_key",
        "contest_name",
        "date",
        "state",
        "county",
        "candidate_name",
        "candidate_party",
        "candidate_votes",
        "candidate_incumbent",
    ]

    summary_fieldnames = [
        "year",
        "contest_key",
        "contest_name",
        "date",
        "state",
        "county_count",
        "statewide_dem_votes",
        "statewide_rep_votes",
        "statewide_other_votes",
        "statewide_total_votes",
        "statewide_two_party_total",
        "statewide_margin_signed",
        "statewide_margin_abs",
        "statewide_margin_pct",
        "statewide_winner_party",
        "statewide_winner_name",
        "statewide_winner_votes",
    ]

    county_rows = []
    candidate_rows = []
    summary_rows = []

    for year, contests in sorted(results_by_year.items(), key=lambda kv: int(kv[0])):
        for contest_key, contest_payload in sorted(contests.items()):
            contest_name = contest_payload.get("contest_name", "")
            date = contest_payload.get("date", "")
            state = contest_payload.get("state", "")
            results = contest_payload.get("results", {})

            dem_sum = 0
            rep_sum = 0
            other_sum = 0
            total_sum = 0
            counties_seen = 0
            statewide_candidates = {}

            for county, row in sorted(results.items()):
                counties_seen += 1
                dem_votes = to_int(row.get("dem_votes", 0))
                rep_votes = to_int(row.get("rep_votes", 0))
                other_votes = to_int(row.get("other_votes", 0))
                total_votes = to_int(row.get("total_votes", 0))

                dem_sum += dem_votes
                rep_sum += rep_votes
                other_sum += other_votes
                total_sum += total_votes

                comp = row.get("competitiveness", {}) or {}
                county_rows.append(
                    {
                        "year": year,
                        "contest_key": contest_key,
                        "contest_name": contest_name,
                        "date": date,
                        "state": state,
                        "county": county,
                        "dem_candidate": row.get("dem_candidate", ""),
                        "rep_candidate": row.get("rep_candidate", ""),
                        "dem_votes": dem_votes,
                        "rep_votes": rep_votes,
                        "other_votes": other_votes,
                        "total_votes": total_votes,
                        "two_party_total": to_int(row.get("two_party_total", 0)),
                        "margin": to_int(row.get("margin", 0)),
                        "margin_pct": row.get("margin_pct", ""),
                        "winner": row.get("winner", ""),
                        "winner_name": row.get("winner_name", ""),
                        "winner_party": row.get("winner_party", ""),
                        "winner_votes": to_int(row.get("winner_votes", 0)),
                        "winner_incumbent": bool(row.get("winner_incumbent", False)),
                        "competitiveness_category": comp.get("category", ""),
                        "competitiveness_party": comp.get("party", ""),
                        "competitiveness_code": comp.get("code", ""),
                        "competitiveness_color": comp.get("color", ""),
                    }
                )

                for candidate_name, candidate_data in (row.get("candidates", {}) or {}).items():
                    votes = to_int((candidate_data or {}).get("votes", 0))
                    party = (candidate_data or {}).get("party", "")
                    incumbent = bool((candidate_data or {}).get("incumbent", False))
                    candidate_rows.append(
                        {
                            "year": year,
                            "contest_key": contest_key,
                            "contest_name": contest_name,
                            "date": date,
                            "state": state,
                            "county": county,
                            "candidate_name": candidate_name,
                            "candidate_party": party,
                            "candidate_votes": votes,
                            "candidate_incumbent": incumbent,
                        }
                    )
                    key = (candidate_name, party)
                    statewide_candidates[key] = statewide_candidates.get(key, 0) + votes

            two_party = dem_sum + rep_sum
            margin_signed = dem_sum - rep_sum
            margin_abs = abs(margin_signed)
            margin_pct = (margin_abs / total_sum * 100.0) if total_sum > 0 else 0.0

            if margin_signed > 0:
                winner_party = "DEMOCRAT"
                winner_votes = dem_sum
            elif margin_signed < 0:
                winner_party = "REPUBLICAN"
                winner_votes = rep_sum
            else:
                winner_party = "TIE"
                winner_votes = max(dem_sum, rep_sum)

            winner_name = "Tie"
            if winner_party in {"DEMOCRAT", "REPUBLICAN"}:
                candidates_for_winner = [
                    (name, votes)
                    for (name, party), votes in statewide_candidates.items()
                    if party == winner_party
                ]
                if candidates_for_winner:
                    winner_name = max(candidates_for_winner, key=lambda x: x[1])[0]

            summary_rows.append(
                {
                    "year": year,
                    "contest_key": contest_key,
                    "contest_name": contest_name,
                    "date": date,
                    "state": state,
                    "county_count": counties_seen,
                    "statewide_dem_votes": dem_sum,
                    "statewide_rep_votes": rep_sum,
                    "statewide_other_votes": other_sum,
                    "statewide_total_votes": total_sum,
                    "statewide_two_party_total": two_party,
                    "statewide_margin_signed": margin_signed,
                    "statewide_margin_abs": margin_abs,
                    "statewide_margin_pct": f"{margin_pct:.2f}",
                    "statewide_winner_party": winner_party,
                    "statewide_winner_name": winner_name,
                    "statewide_winner_votes": winner_votes,
                }
            )

    with COUNTY_ROWS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=county_fieldnames)
        w.writeheader()
        w.writerows(county_rows)

    with CANDIDATE_ROWS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=candidate_fieldnames)
        w.writeheader()
        w.writerows(candidate_rows)

    with SUMMARY_ROWS_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=summary_fieldnames)
        w.writeheader()
        w.writerows(summary_rows)

    print(f"Wrote {COUNTY_ROWS_CSV} ({len(county_rows)} rows)")
    print(f"Wrote {CANDIDATE_ROWS_CSV} ({len(candidate_rows)} rows)")
    print(f"Wrote {SUMMARY_ROWS_CSV} ({len(summary_rows)} rows)")


if __name__ == "__main__":
    main()
