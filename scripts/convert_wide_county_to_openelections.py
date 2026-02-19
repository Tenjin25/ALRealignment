from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


PARTY_MAP = {
    "D": "DEM",
    "R": "REP",
    "I": "IND",
    "L": "LIB",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if text.lower().startswith("unnamed:"):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_candidate_and_party(raw_candidate: str) -> tuple[str, str]:
    candidate = clean_text(raw_candidate)
    if not candidate:
        return "", ""

    match = re.search(r"\(([A-Za-z]+)\)\s*$", candidate)
    if match:
        party_raw = match.group(1).upper()
        party = PARTY_MAP.get(party_raw, party_raw)
        candidate = re.sub(r"\s*\([A-Za-z]+\)\s*$", "", candidate).strip()
        return candidate, party

    if "write-in" in candidate.lower():
        return "Write-ins", "NON"

    return candidate, ""


def normalize_office(raw_office: str) -> tuple[str, str]:
    office = clean_text(raw_office)
    if not office:
        return "", ""

    house_match = re.search(
        r"U\.S\.\s*House(?:\s+\d+(?:st|nd|rd|th)\s+District|\s+District\s+(\d+))",
        office,
        flags=re.IGNORECASE,
    )
    if house_match:
        district = ""
        explicit = house_match.group(1)
        if explicit:
            district = explicit
        else:
            fallback = re.search(r"U\.S\.\s*House\s+(\d+)(?:st|nd|rd|th)\s+District", office, flags=re.IGNORECASE)
            if fallback:
                district = fallback.group(1)
        return "U.S. House", district

    return office, ""


def parse_votes(raw_votes: object) -> str:
    text = clean_text(raw_votes).replace(",", "")
    if not text:
        return ""
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        number = float(text)
        if number.is_integer():
            return str(int(number))
        return str(number)
    return ""


def convert_file(path: Path) -> list[dict[str, str]]:
    df = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    if df.empty or len(df.index) < 3 or len(df.columns) < 2:
        return []

    offices_raw = [clean_text(v) for v in df.iloc[0].tolist()]
    candidates_raw = [clean_text(v) for v in df.iloc[1].tolist()]

    offices_filled: list[str] = []
    current_office = ""
    for office in offices_raw:
        if office:
            current_office = office
        offices_filled.append(current_office)

    # Some exports place a report title in column 0 and leave the first
    # candidate office cells blank. Backfill those leading columns with the
    # first real office header.
    first_real_office_idx = None
    for i in range(1, len(offices_raw)):
        if offices_raw[i]:
            first_real_office_idx = i
            break
    if first_real_office_idx and first_real_office_idx > 1:
        first_real_office = offices_raw[first_real_office_idx]
        for i in range(1, first_real_office_idx):
            offices_filled[i] = first_real_office

    rows: list[dict[str, str]] = []
    for r in range(2, len(df.index)):
        county = clean_text(df.iat[r, 0])
        if not county or county.lower() == "county":
            continue

        for c in range(1, len(df.columns)):
            office, district = normalize_office(offices_filled[c] if c < len(offices_filled) else "")
            candidate, party = parse_candidate_and_party(candidates_raw[c] if c < len(candidates_raw) else "")
            votes = parse_votes(df.iat[r, c])
            if not office or not candidate or not votes:
                continue

            rows.append(
                {
                    "county": county.strip(),
                    "precinct": "",
                    "office": office,
                    "district": district,
                    "party": party,
                    "candidate": candidate,
                    "votes": votes,
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert wide county CSV election data to OpenElections long format.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input CSV paths.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    args = parser.parse_args()

    all_rows: list[dict[str, str]] = []
    for input_path in args.inputs:
        all_rows.extend(convert_file(Path(input_path)))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(all_rows, columns=["county", "precinct", "office", "district", "party", "candidate", "votes"])
    result.to_csv(output, index=False)
    print(f"Wrote {len(result)} rows to {output}")


if __name__ == "__main__":
    main()
