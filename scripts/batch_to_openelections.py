from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

import pandas as pd
from pandas.errors import EmptyDataError


TARGET_COLUMNS = ["county", "precinct", "office", "district", "party", "candidate", "votes"]

PARTY_MAP = {
    "D": "DEM",
    "R": "REP",
    "I": "IND",
    "L": "LIB",
    "DEM": "DEM",
    "REP": "REP",
    "LIB": "LIB",
    "IND": "IND",
    "WI": "NON",
    "NON": "NON",
    "TBC": "",
}


def clean_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\ufeff", "").strip()
    if text.lower().startswith("unnamed:"):
        return ""
    return re.sub(r"\s+", " ", text).strip()


def parse_votes(value: object) -> str:
    text = clean_text(value).replace(",", "")
    if not text:
        return ""
    if text.upper() == "NR":
        return ""
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        n = float(text)
        return str(int(n)) if n.is_integer() else str(n)
    return ""


def normalize_party(value: str) -> str:
    raw = clean_text(value).upper()
    return PARTY_MAP.get(raw, raw)


def normalize_candidate(value: str) -> str:
    candidate = clean_text(value)
    if candidate.upper() == "WRITE-IN":
        return "Write-ins"
    return candidate


def parse_candidate_and_party(value: str, fallback_party: str = "") -> tuple[str, str]:
    candidate = clean_text(value)
    if not candidate:
        return "", normalize_party(fallback_party)

    match = re.search(r"\(([A-Za-z]+)\)\s*$", candidate)
    if match:
        party = normalize_party(match.group(1))
        candidate = re.sub(r"\s*\([A-Za-z]+\)\s*$", "", candidate).strip()
        return normalize_candidate(candidate), party

    if candidate.lower() == "write-in":
        return "Write-ins", "NON"

    return candidate, normalize_party(fallback_party)


def infer_office_from_name(stem: str) -> str:
    s = stem.lower()
    if "ltgovernor" in s:
        return "Lieutenant Governor"
    if "governor" in s:
        return "Governor"
    if "president" in s:
        return "President"
    if "ussenate" in s or "ussenate" in s:
        return "U.S. Senate"
    if "attorneygeneral" in s:
        return "Attorney General"
    if "treasurer" in s:
        return "State Treasurer"
    if "auditor" in s:
        return "State Auditor"
    if "commissionerag-and-ind" in s or "agind" in s:
        return "Commissioner of Agriculture and Industries"
    return "Office"


def normalize_office(value: str) -> tuple[str, str]:
    office = clean_text(value)
    district = ""

    if not office:
        return "", ""

    office_u = office.upper()
    office_u = office_u.replace("UNITED STATES SENATOR", "U.S. Senate")
    office_u = office_u.replace("UNITED STATES HOUSE", "U.S. House")
    office_u = office_u.replace("ASSOCIATE JUSTICE, SUPREME COURT", "Associate Justice, Supreme Court")
    office_u = office_u.replace("SECRETARY OF STATE", "Secretary of State")
    office_u = office_u.replace("STATE TREASURER", "State Treasurer")
    office_u = office_u.replace("ATTORNEY GENERAL", "Attorney General")
    office_u = office_u.replace("LIEUTENANT GOVERNOR", "Lieutenant Governor")

    house_m = re.search(
        r"U\.S\.\s*HOUSE(?:\s+DISTRICT\s+(\d+)|\s+(\d+)(?:ST|ND|RD|TH)\s+DISTRICT)",
        office_u,
    )
    if house_m:
        district = house_m.group(1) or house_m.group(2) or ""
        return "U.S. House", district

    if office_u == "UNITED STATES SENATOR":
        return "U.S. Senate", ""

    return office_u.title().replace("Us", "U.S.").replace("Of", "of"), district


def build_row(county: str, precinct: str, office_raw: str, candidate_raw: str, votes_raw: object, party_hint: str = "") -> dict[str, str] | None:
    county = clean_text(county)
    if not county or county.upper() in {"STATE TOTAL", "COUNTY"}:
        return None

    votes = parse_votes(votes_raw)
    if not votes:
        return None

    office, district = normalize_office(office_raw)
    candidate, party = parse_candidate_and_party(candidate_raw, party_hint)
    if not office or not candidate:
        return None

    return {
        "county": county,
        "precinct": clean_text(precinct),
        "office": office,
        "district": district,
        "party": party,
        "candidate": candidate,
        "votes": votes,
    }


def looks_like_openelections(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    row0 = [clean_text(x).lower() for x in df.iloc[0].tolist()]
    return row0[:7] == TARGET_COLUMNS


def parse_two_row_county(df: pd.DataFrame) -> list[dict[str, str]] | None:
    if len(df.index) < 3:
        return None
    if clean_text(df.iat[1, 0]).lower() != "county":
        return None

    offices_raw = [clean_text(v) for v in df.iloc[0].tolist()]
    candidates = [clean_text(v) for v in df.iloc[1].tolist()]

    offices: list[str] = []
    current = ""
    for v in offices_raw:
        if v:
            current = v
        offices.append(current)

    first_real = next((i for i in range(1, len(offices_raw)) if offices_raw[i]), None)
    if first_real and first_real > 1:
        for i in range(1, first_real):
            offices[i] = offices_raw[first_real]

    out: list[dict[str, str]] = []
    for r in range(2, len(df.index)):
        county = clean_text(df.iat[r, 0])
        for c in range(1, len(df.columns)):
            row = build_row(
                county=county,
                precinct="",
                office_raw=offices[c] if c < len(offices) else "",
                candidate_raw=candidates[c] if c < len(candidates) else "",
                votes_raw=df.iat[r, c],
            )
            if row:
                out.append(row)
    return out


def parse_one_row_county(df: pd.DataFrame, default_office: str) -> list[dict[str, str]] | None:
    if len(df.index) < 2:
        return None
    if clean_text(df.iat[0, 0]).lower() != "county":
        return None

    headers = [clean_text(v) for v in df.iloc[0].tolist()]
    out: list[dict[str, str]] = []
    for r in range(1, len(df.index)):
        county = clean_text(df.iat[r, 0])
        for c in range(1, len(df.columns)):
            row = build_row(
                county=county,
                precinct="",
                office_raw=default_office,
                candidate_raw=headers[c] if c < len(headers) else "",
                votes_raw=df.iat[r, c],
            )
            if row:
                out.append(row)
    return out


def parse_president_two_row(df: pd.DataFrame, default_office: str) -> list[dict[str, str]] | None:
    if len(df.index) < 3:
        return None
    if clean_text(df.iat[0, 0]) or clean_text(df.iat[1, 0]):
        return None
    # First row has candidate+party; row2 is first county.
    if not clean_text(df.iat[2, 0]):
        return None

    row0 = [clean_text(v) for v in df.iloc[0].tolist()]
    row1 = [clean_text(v) for v in df.iloc[1].tolist()]

    # Forward-fill office names across columns.
    offices: list[str] = []
    current_office = ""
    for v in row0:
        if v:
            current_office = v
        offices.append(current_office)

    # If row1 contains likely candidate labels, use it for candidate names.
    row1_candidate_like = any(
        ("(" in v and ")" in v) or v.lower() == "write-in"
        for v in row1[1:]
        if v
    )
    use_row1_candidates = row1_candidate_like

    out: list[dict[str, str]] = []
    for r in range(2, len(df.index)):
        county = clean_text(df.iat[r, 0])
        for c in range(1, len(df.columns)):
            row = build_row(
                county=county,
                precinct="",
                office_raw=(offices[c] if c < len(offices) and offices[c] else default_office),
                candidate_raw=(
                    row1[c] if use_row1_candidates and c < len(row1) else (row0[c] if c < len(row0) else "")
                ),
                votes_raw=df.iat[r, c],
            )
            if row:
                out.append(row)
    return out


def parse_three_header_county(df: pd.DataFrame) -> list[dict[str, str]] | None:
    if len(df.index) < 5:
        return None
    if clean_text(df.iat[2, 1]).upper() not in {"DEM", "REP", "LIB", "WI", "TBC", "NON", "IND"}:
        return None
    if clean_text(df.iat[3, 0]).upper() not in {"STATE TOTAL", "AUTAUGA"}:
        return None

    offices = [clean_text(v) for v in df.iloc[1].tolist()]
    parties = [clean_text(v) for v in df.iloc[2].tolist()]
    candidates = [clean_text(v) for v in df.iloc[3].tolist()]

    out: list[dict[str, str]] = []
    for r in range(4, len(df.index)):
        county = clean_text(df.iat[r, 0])
        for c in range(1, len(df.columns)):
            row = build_row(
                county=county,
                precinct="",
                office_raw=offices[c] if c < len(offices) else "",
                candidate_raw=candidates[c] if c < len(candidates) else "",
                party_hint=parties[c] if c < len(parties) else "",
                votes_raw=df.iat[r, c],
            )
            if row:
                out.append(row)
    return out


def parse_master_county(df: pd.DataFrame) -> list[dict[str, str]] | None:
    if len(df.index) < 7:
        return None
    if clean_text(df.iat[3, 1]).upper() != "OFFICE":
        return None

    counties = [clean_text(v) for v in df.iloc[4].tolist()]
    out: list[dict[str, str]] = []
    for r in range(5, len(df.index)):
        office = clean_text(df.iat[r, 1])
        party = clean_text(df.iat[r, 2])
        candidate = clean_text(df.iat[r, 3])
        if not office or not candidate:
            continue
        for c in range(5, len(df.columns)):
            row = build_row(
                county=counties[c] if c < len(counties) else "",
                precinct="",
                office_raw=office,
                candidate_raw=candidate,
                party_hint=party,
                votes_raw=df.iat[r, c],
            )
            if row:
                out.append(row)
    return out


def parse_precinct_split(files: Iterable[Path]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for path in files:
        df = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
        if len(df.index) < 4:
            continue
        if clean_text(df.iat[2, 0]).lower() != "county code" or clean_text(df.iat[2, 1]).lower() != "county":
            continue

        precinct_names = [clean_text(v) for v in df.iloc[1].tolist()]
        for r in range(3, len(df.index)):
            county = clean_text(df.iat[r, 1]).title()
            office = clean_text(df.iat[r, 2])
            party = clean_text(df.iat[r, 3])
            candidate = clean_text(df.iat[r, 4])
            for c in range(6, len(df.columns)):
                row = build_row(
                    county=county,
                    precinct=precinct_names[c] if c < len(precinct_names) else "",
                    office_raw=office,
                    candidate_raw=candidate,
                    party_hint=party,
                    votes_raw=df.iat[r, c],
                )
                if row:
                    out.append(row)
    return out


def convert_single_file(path: Path) -> list[dict[str, str]]:
    try:
        df = pd.read_csv(path, header=None, dtype=str, keep_default_na=False)
    except EmptyDataError:
        return []
    if df.empty or looks_like_openelections(df):
        return []

    default_office = infer_office_from_name(path.stem)
    parsers = [
        parse_master_county,
        parse_three_header_county,
        parse_two_row_county,
        lambda x: parse_one_row_county(x, default_office),
        lambda x: parse_president_two_row(x, default_office),
    ]
    for parser in parsers:
        rows = parser(df)
        if rows:
            return rows
    return []


def write_output(rows: list[dict[str, str]], output_path: Path) -> int:
    if not rows:
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=TARGET_COLUMNS)
    df.to_csv(output_path, index=False)
    return len(df.index)


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-convert election CSVs to OpenElections long format.")
    parser.add_argument("--data-dir", default="data", help="Input data directory")
    parser.add_argument("--output-dir", default="data/openelections", help="Output directory")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_csv = sorted(p for p in data_dir.glob("*.csv"))
    summary: list[tuple[str, int]] = []

    split_prefix = "2002-GeneralElection-PrecinctLevel_0-"
    split_files = [p for p in all_csv if p.name.startswith(split_prefix)]
    if split_files:
        rows = parse_precinct_split(split_files)
        out_path = output_dir / "20021105__al__general__precinct.csv"
        count = write_output(rows, out_path)
        summary.append((out_path.name, count))

    skip_names = {p.name for p in split_files}
    skip_names.add("20201103__al__general__precinct.csv")

    for path in all_csv:
        if path.name in skip_names:
            continue
        rows = convert_single_file(path)
        if not rows:
            continue
        out_path = output_dir / path.name
        count = write_output(rows, out_path)
        summary.append((out_path.name, count))

    summary_path = output_dir / "_conversion_summary.csv"
    pd.DataFrame(summary, columns=["file", "rows"]).to_csv(summary_path, index=False)
    print(f"Wrote {len(summary)} file(s) to {output_dir}")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
