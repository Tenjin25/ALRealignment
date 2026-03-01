import csv
import json
import re
from pathlib import Path


INPUT_JSON = Path("data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json")
OUTPUT_DIR = Path("data/openelections_office_normalized_2016_2024")

YEAR_MIN = 2016
YEAR_MAX = 2024


PARTY_TO_CODE = {
    "DEMOCRAT": "DEM",
    "REPUBLICAN": "REP",
    "LIBERTARIAN": "LIB",
    "INDEPENDENT": "IND",
    "NONPARTISAN": "NON",
    "OTHER": "OTH",
}


def office_slug_from_contest_key(contest_key: str) -> str:
    base = re.sub(r"_\d{4}$", "", contest_key)
    mapping = {
        "president": "president",
        "us_senate": "ussenate",
        "governor": "governor",
        "lieutenant_governor": "ltgovernor",
        "attorney_general": "attorneygeneral",
        "secretary_of_state": "secretaryofstate",
        "state_treasurer": "treasurer",
        "state_auditor": "auditor",
        "commissioner_of_agriculture": "commissionerag",
        "public_service_commissioner": "publicservicecommission",
    }
    return mapping.get(base, base.replace("_", ""))


def party_code_from_name(name: str) -> str:
    key = str(name).strip().upper()
    return PARTY_TO_CODE.get(key, key[:3] if key else "OTH")


def main() -> None:
    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    by_year = data.get("results_by_year", {})
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    files_written = 0
    rows_written = 0

    for year_str, contests in sorted(by_year.items(), key=lambda kv: int(kv[0])):
        year = int(year_str)
        if year < YEAR_MIN or year > YEAR_MAX:
            continue

        for contest_key, payload in sorted(contests.items()):
            results = payload.get("results", {})
            if not isinstance(results, dict) or not results:
                continue

            ymd = str(payload.get("date", f"{year_str}0101"))
            office_slug = office_slug_from_contest_key(contest_key)
            out_name = f"{ymd}__al__general__county__{office_slug}.csv"
            out_path = OUTPUT_DIR / out_name

            rows = []
            for county, county_row in sorted(results.items()):
                candidates = county_row.get("candidates", {}) or {}
                for candidate_name, candidate_data in sorted(candidates.items()):
                    votes = int((candidate_data or {}).get("votes", 0) or 0)
                    if votes <= 0:
                        continue
                    party_name = (candidate_data or {}).get("party", "")
                    rows.append(
                        {
                            "county": county,
                            "precinct": "",
                            "office": payload.get("contest_name", ""),
                            "district": "",
                            "party": party_code_from_name(party_name),
                            "candidate": candidate_name,
                            "votes": votes,
                        }
                    )

            if not rows:
                continue

            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["county", "precinct", "office", "district", "party", "candidate", "votes"],
                )
                writer.writeheader()
                writer.writerows(rows)

            files_written += 1
            rows_written += len(rows)

    print(f"Wrote {files_written} files to {OUTPUT_DIR}")
    print(f"Total rows: {rows_written}")


if __name__ == "__main__":
    main()
