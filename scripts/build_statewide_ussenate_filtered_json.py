from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd


BASE_JSON = Path("data/results_by_year_grouped.final.json")
OUTPUT_JSON = Path("data/results_by_year_grouped.statewide_plus_ussenate_1968_2026.json")
PRESIDENT_CSV_DIR = Path("data/openelections")
PRESIDENT_OFFICE_CSV_DIR = Path("data/openelections_office_normalized_2016_2024")
US_SENATE_CSV_DIR = Path("data/openelections_office_normalized")

DATA_DIR = Path("data")
YEAR_MIN = 1968
YEAR_MAX = 2026

COUNTIES = {
    "AUTAUGA",
    "BALDWIN",
    "BARBOUR",
    "BIBB",
    "BLOUNT",
    "BULLOCK",
    "BUTLER",
    "CALHOUN",
    "CHAMBERS",
    "CHEROKEE",
    "CHILTON",
    "CHOCTAW",
    "CLARKE",
    "CLAY",
    "CLEBURNE",
    "COFFEE",
    "COLBERT",
    "CONECUH",
    "COOSA",
    "COVINGTON",
    "CRENSHAW",
    "CULLMAN",
    "DALE",
    "DALLAS",
    "DEKALB",
    "ELMORE",
    "ESCAMBIA",
    "ETOWAH",
    "FAYETTE",
    "FRANKLIN",
    "GENEVA",
    "GREENE",
    "HALE",
    "HENRY",
    "HOUSTON",
    "JACKSON",
    "JEFFERSON",
    "LAMAR",
    "LAUDERDALE",
    "LAWRENCE",
    "LEE",
    "LIMESTONE",
    "LOWNDES",
    "MACON",
    "MADISON",
    "MARENGO",
    "MARION",
    "MARSHALL",
    "MOBILE",
    "MONROE",
    "MONTGOMERY",
    "MORGAN",
    "PERRY",
    "PICKENS",
    "PIKE",
    "RANDOLPH",
    "RUSSELL",
    "SHELBY",
    "ST CLAIR",
    "SUMTER",
    "TALLADEGA",
    "TALLAPOOSA",
    "TUSCALOOSA",
    "WALKER",
    "WASHINGTON",
    "WILCOX",
    "WINSTON",
}

COUNTY_CANONICAL_BY_COMPACT = {c.replace(" ", ""): c for c in COUNTIES}
COUNTY_ALIASES_COMPACT = {
    "STCLAIR": "ST CLAIR",
    "STCLAIRCOUNTY": "ST CLAIR",
    "SAINTCLAIR": "ST CLAIR",
    "SAINTCLAIRCOUNTY": "ST CLAIR",
}

PARTY_CODE_TO_NAME = {
    "D": "DEMOCRAT",
    "DEM": "DEMOCRAT",
    "DEMOCRAT": "DEMOCRAT",
    "R": "REPUBLICAN",
    "REP": "REPUBLICAN",
    "REPUBLICAN": "REPUBLICAN",
    "AR": "REPUBLICAN",
    "L": "LIBERTARIAN",
    "LIB": "LIBERTARIAN",
    "LIBERTARIAN": "LIBERTARIAN",
    "I": "INDEPENDENT",
    "IND": "INDEPENDENT",
    "INDEPENDENT": "INDEPENDENT",
    "NON": "NONPARTISAN",
    "NP": "NONPARTISAN",
    "NONPARTISAN": "NONPARTISAN",
    "WI": "NONPARTISAN",
    "WRITE-IN": "NONPARTISAN",
    "WRITE-INS": "NONPARTISAN",
}

NAME_OVERRIDES = {
    ("president", "1976", "CARTER"): "Jimmy Carter",
    ("president", "1976", "FORD"): "Gerald Ford",
    ("president", "1980", "CARTER"): "Jimmy Carter",
    ("president", "1980", "REAGAN"): "Ronald Reagan",
    ("president", "1980", "ANDERSON"): "John B. Anderson",
    ("president", "1984", "MONDALE"): "Walter Mondale",
    ("president", "1984", "REAGAN"): "Ronald Reagan",
    ("president", "1988", "BUSH"): "George H. W. Bush",
    ("president", "1988", "DUKAKIS"): "Michael Dukakis",
    ("president", "1992", "BUSH"): "George H. W. Bush",
    ("president", "1992", "CLINTON"): "Bill Clinton",
    ("president", "1992", "PEROT"): "Ross Perot",
    ("president", "1996", "CLINTON"): "Bill Clinton",
    ("president", "1996", "DOLE"): "Bob Dole",
    ("president", "1996", "PEROT"): "Ross Perot",
    ("president", "2000", "BUSH"): "George W. Bush",
    ("president", "2000", "GORE"): "Al Gore",
    ("president", "2004", "BUSH"): "George W. Bush",
    ("president", "2004", "KERRY"): "John Kerry",
    ("us_senate", "2004", "SHELBY"): "Richard Shelby",
    ("us_senate", "2004", "SOWELL"): "Wayne Sowell",
    ("us_senate", "2010", "BARNES"): "William G. Barnes",
    ("us_senate", "2010", "SHELBY"): "Richard Shelby",
    ("governor", "2006", "RILEY"): "Bob Riley",
    ("governor", "2006", "BAXLEY"): "Lucy Baxley",
    ("commissioner_of_agriculture", "2006", "SPARKS"): "Ron Sparks",
    ("commissioner_of_agriculture", "2006", "LIPSCOMB"): "Nathan Lipscomb",
    ("commissioner_of_agriculture", "2010", "ZORN"): "Glen Zorn",
    ("commissioner_of_agriculture", "2010", "MCMILLAN"): "John McMillan",
    ("attorney_general", "2010", "STRANGE"): "Luther Strange",
    ("attorney_general", "2010", "ANDERSON"): "James H. Anderson",
    ("lieutenant_governor", "2010", "IVEY"): "Kay Ivey",
    ("lieutenant_governor", "2010", "FOLSOM"): "Jim Folsom Jr.",
}

AGGREGATE_CANDIDATE_LABELS = {
    "TOTAL",
    "TOTALS",
    "MARGIN",
    "CALCULATED",
    "REPORTED",
    "STATE TOTAL",
}

# Known bad rows in normalized presidential office extracts.
# 2016 and 2024 files include Twinkle Andress Cavanaugh (PSC candidate)
# mixed into president rows due to a spreadsheet layout issue.
PRESIDENT_CANDIDATE_EXCLUDES = {
    ("2016", "TWINKLE ANDRESS CAVANAUGH"),
    ("2024", "TWINKLE ANDRESS CAVANAUGH"),
}


def normalize_county_name(name: str) -> str:
    s = re.sub(r"[^A-Za-z ]+", " ", name).strip().upper()
    s = re.sub(r"\s+", " ", s)
    return s


def canonical_county(name: str) -> str:
    raw = str(name).strip()
    if not raw:
        return ""
    if raw.lower() in {"total", "margin", "state total"}:
        return ""
    norm = normalize_county_name(raw)
    compact = norm.replace(" ", "")
    if compact in COUNTY_ALIASES_COMPACT:
        return COUNTY_ALIASES_COMPACT[compact].title()
    if compact in COUNTY_CANONICAL_BY_COMPACT:
        return COUNTY_CANONICAL_BY_COMPACT[compact].title()
    # Explicitly reject non-county rows (e.g., totals/certified lines)
    if any(tok in compact for tok in ("TOTAL", "CERTIFIED", "MARGIN", "STATEWIDE")):
        return ""
    return ""


def county_from_path(path: Path) -> str | None:
    text = normalize_county_name(path.stem.replace("-", " ").replace("_", " "))
    compact_text = text.replace(" ", "")
    for alias_compact, canonical in COUNTY_ALIASES_COMPACT.items():
        if alias_compact in compact_text:
            return canonical.title()
    for c in COUNTIES:
        if c.replace(" ", "") in compact_text:
            return c.title()
    return None


def year_from_path(path: Path) -> int | None:
    m4 = re.findall(r"(19\d{2}|20\d{2})", path.as_posix())
    if m4:
        return int(m4[-1])
    m2 = re.findall(r"(?<!\d)(\d{2})(?!\d)", path.as_posix())
    if m2:
        yy = int(m2[-1])
        return 2000 + yy if yy <= 30 else 1900 + yy
    return None


def contest_key_from_title(title: str) -> tuple[str, str] | None:
    t = title.upper()
    t = re.sub(r"\s+", " ", t).strip()

    # Check PSC *before* the generic PRESIDENT check because Alabama uses
    # titles like "PRESIDENT, PUBLIC SERVICE COMMISSION" which start with
    # "PRESIDENT" but are not presidential elections.
    if "PUBLIC SERVICE COMMISSION" in t:
        return "public_service_commissioner", "Public Service Commissioner"
    if "PRESIDENT" in t and "VICE-PRESIDENT" in t:
        return "president", "President"
    if "PRESIDENT" in t and "VICE PRESIDENT" in t:
        return "president", "President"
    if "PRESIDENT AND VICE PRESIDENT" in t:
        return "president", "President"
    if t.startswith("PRESIDENT"):
        return "president", "President"
    if "UNITED STATES SENATOR" in t or "U.S. SENATE" in t:
        return "us_senate", "U.S. Senate"
    if "LIEUTENANT GOVERNOR" in t:
        return "lieutenant_governor", "Lieutenant Governor"
    if "ATTORNEY GENERAL" in t:
        return "attorney_general", "Attorney General"
    if "SECRETARY OF STATE" in t:
        return "secretary_of_state", "Secretary of State"
    if "STATE TREASURER" in t or t.startswith("TREASURER"):
        return "state_treasurer", "State Treasurer"
    if "STATE AUDITOR" in t or t.startswith("AUDITOR"):
        return "state_auditor", "State Auditor"
    if "AGRICULTURE" in t and "COMMISSIONER" in t:
        return "commissioner_of_agriculture", "Commissioner of Agriculture"
    if "GOVERNOR" in t and "LIEUTENANT" not in t:
        return "governor", "Governor"
    return None


def parse_int(v: Any) -> int | None:
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    n = float(s)
    if not n.is_integer():
        return None
    return int(n)


def is_aggregate_candidate(name: str) -> bool:
    n = normalize_candidate_name(name).upper().strip()
    return n in AGGREGATE_CANDIDATE_LABELS


def is_excluded_president_candidate(year: str, candidate: str) -> bool:
    n = normalize_candidate_name(candidate).upper().strip()
    return (str(year), n) in PRESIDENT_CANDIDATE_EXCLUDES


def party_name(code: str, candidate: str) -> str:
    c = (code or "").strip().upper()
    if c in PARTY_CODE_TO_NAME:
        return PARTY_CODE_TO_NAME[c]
    if candidate.strip().upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"}:
        return "NONPARTISAN"
    return "OTHER"


def split_candidate_and_party(candidate: str, party_code: str) -> tuple[str, str]:
    cand = str(candidate).strip()
    code = str(party_code).strip().upper()

    if not code and cand:
        m_dash = re.search(r"\s-\s([A-Za-z.]+)\s*$", cand)
        if m_dash:
            code = m_dash.group(1).strip().upper().rstrip(".")
            cand = cand[: m_dash.start()].strip()
        else:
            m_paren = re.search(r"\(([A-Za-z.]+)\)\s*$", cand)
            if m_paren:
                code = m_paren.group(1).strip().upper().rstrip(".")
                cand = re.sub(r"\s*\([A-Za-z.]+\)\s*$", "", cand).strip()

    cand = normalize_candidate_name(cand)
    return cand, code


def normalize_candidate_name(name: str) -> str:
    raw = str(name).strip()
    if not raw:
        return raw
    suffixes = {"JR", "JR.", "SR", "SR.", "II", "III", "IV", "V"}
    if raw.count(",") == 1:
        left, right = [p.strip() for p in raw.split(",", 1)]
        if left and right and right.upper() not in suffixes:
            raw = f"{right} {left}"
    letters = [ch for ch in raw if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters):
        raw = raw.title()
    return re.sub(r"\s+", " ", raw).strip()


def enrich_candidate_name(name: str, contest_key: str, year: str) -> str:
    n = normalize_candidate_name(name)
    if not n:
        return n
    if len(n.split()) != 1:
        return n
    return NAME_OVERRIDES.get((contest_key, str(year), n.upper()), n)


def normalize_contest_payload_names(payload: dict[str, Any], year: str, contest_key: str) -> dict[str, Any]:
    results = payload.get("results")
    if not isinstance(results, dict):
        return payload

    for county, row in results.items():
        if not isinstance(row, dict):
            continue

        for field in ("dem_candidate", "rep_candidate", "winner_name"):
            if field in row:
                row[field] = enrich_candidate_name(row.get(field, ""), contest_key, year)

        old_candidates = row.get("candidates", {})
        if isinstance(old_candidates, dict):
            new_candidates: dict[str, Any] = {}
            for old_name, details in old_candidates.items():
                new_name = enrich_candidate_name(old_name, contest_key, year)
                if new_name not in new_candidates:
                    new_candidates[new_name] = details
                    continue
                existing = new_candidates[new_name]
                if isinstance(existing, dict) and isinstance(details, dict):
                    existing["votes"] = int(existing.get("votes", 0)) + int(details.get("votes", 0))
            row["candidates"] = new_candidates

        results[county] = row

    payload["results"] = results
    return payload


def competitiveness(margin_pct: float, winner_party: str) -> dict[str, str]:
    if winner_party not in {"DEMOCRAT", "REPUBLICAN"}:
        return {"category": "Tossup", "party": "TIE", "code": "TOSSUP", "color": "#f7f7f7"}
    if margin_pct >= 40:
        cat, color = "Annihilation", "#08306b" if winner_party == "DEMOCRAT" else "#67000d"
    elif margin_pct >= 30:
        cat, color = "Dominant", "#08519c" if winner_party == "DEMOCRAT" else "#a50f15"
    elif margin_pct >= 20:
        cat, color = "Stronghold", "#3182bd" if winner_party == "DEMOCRAT" else "#cb181d"
    elif margin_pct >= 10:
        cat, color = "Safe", "#6baed6" if winner_party == "DEMOCRAT" else "#ef3b2c"
    elif margin_pct >= 5.5:
        cat, color = "Likely", "#9ecae1" if winner_party == "DEMOCRAT" else "#fb6a4a"
    elif margin_pct >= 1:
        cat, color = "Lean", "#c6dbef" if winner_party == "DEMOCRAT" else "#fcae91"
    elif margin_pct >= 0.5:
        cat, color = "Tilt", "#e1f5fe" if winner_party == "DEMOCRAT" else "#fee8c8"
    else:
        return {"category": "Tossup", "party": winner_party, "code": f"{winner_party}_TOSSUP", "color": "#f7f7f7"}
    return {"category": cat, "party": winner_party, "code": f"{winner_party}_{cat.upper()}", "color": color}


def margin_label(margin: int, total: int) -> str:
    if total <= 0:
        return "TIE+0.00"
    pct = abs(margin) / total * 100.0
    if margin > 0:
        return f"D+{pct:.2f}"
    if margin < 0:
        return f"R+{pct:.2f}"
    return "TIE+0.00"


def parse_precinct_workbook(path: Path) -> list[dict[str, Any]]:
    county = county_from_path(path)
    year = year_from_path(path)
    if not county or not year or not (YEAR_MIN <= year <= YEAR_MAX):
        return []

    try:
        df = pd.read_excel(path, dtype=str)
    except Exception:
        return []

    # Supported layout: Contest Title / Party / Candidate + precinct vote columns.
    cols = {c.strip().upper(): c for c in df.columns}
    if "CONTEST TITLE" not in cols or "CANDIDATE" not in cols:
        return []

    contest_col = cols["CONTEST TITLE"]
    candidate_col = cols["CANDIDATE"]
    party_col = cols.get("PARTY")

    fixed_cols = {contest_col, candidate_col}
    if party_col:
        fixed_cols.add(party_col)
    # Optional one-column total provided by some files.
    total_col = None
    for c in df.columns:
        cu = c.strip().upper()
        if cu in {"TOTAL OF VOTES", "TOTAL NUMBER OF VOTES", "TOTAL VOTES"}:
            total_col = c
            fixed_cols.add(c)
            break

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        contest_title = str(r.get(contest_col, "")).strip()
        candidate = str(r.get(candidate_col, "")).strip()
        if not contest_title or not candidate:
            continue
        if candidate.upper() in {"OVER VOTES", "UNDER VOTES", "UNDER VOTE", "OVER VOTE", "BALLOTS CAST - TOTAL", "REGISTERED VOTERS - TOTAL"}:
            continue
        if "STRAIGHT PARTY" in contest_title.upper():
            continue

        ck = contest_key_from_title(contest_title)
        if not ck:
            continue
        contest_key, contest_name = ck

        p = str(r.get(party_col, "") if party_col else "").strip()
        candidate, parsed_code = split_candidate_and_party(candidate, p)
        if is_aggregate_candidate(candidate):
            continue
        p_name = party_name(parsed_code, candidate)

        votes = None
        if total_col:
            votes = parse_int(r.get(total_col, ""))
        if votes is None:
            s = 0
            for c in df.columns:
                if c in fixed_cols:
                    continue
                n = parse_int(r.get(c, ""))
                if n is not None:
                    s += n
            votes = s
        if votes <= 0:
            continue

        rows.append(
            {
                "year": str(year),
                "contest_key": contest_key,
                "contest_name": contest_name,
                "county": county,
                "party": p_name,
                "candidate": "Write-ins" if candidate.upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"} else candidate,
                "votes": votes,
            }
        )
    return rows


def build_payload(rows: list[dict[str, Any]], year: str, contest_key: str, contest_name: str) -> dict[str, Any]:
    county_bins: dict[str, dict[str, Any]] = {}
    for row in rows:
        c = row["county"]
        b = county_bins.setdefault(
            c,
            {
                "party_votes": defaultdict(int),
                "candidates": {},
                "dem_candidate": "",
                "rep_candidate": "",
            },
        )
        p = row["party"]
        cand = row["candidate"]
        votes = int(row["votes"])
        b["party_votes"][p] += votes
        if cand not in b["candidates"]:
            b["candidates"][cand] = {"votes": 0, "party": p, "incumbent": False}
        b["candidates"][cand]["votes"] += votes
        if p == "DEMOCRAT" and not b["dem_candidate"]:
            b["dem_candidate"] = cand
        if p == "REPUBLICAN" and not b["rep_candidate"]:
            b["rep_candidate"] = cand

    results: dict[str, Any] = {}
    for county, b in county_bins.items():
        dem = int(b["party_votes"].get("DEMOCRAT", 0))
        rep = int(b["party_votes"].get("REPUBLICAN", 0))
        total = int(sum(b["party_votes"].values()))
        other = int(total - dem - rep)
        margin_signed = dem - rep
        margin_abs = abs(margin_signed)
        two_party = dem + rep
        margin_pct_num = (margin_abs / total * 100.0) if total > 0 else 0.0

        if margin_signed > 0:
            wp, wn, wv = "DEMOCRAT", b["dem_candidate"] or "Democratic Candidate", dem
        elif margin_signed < 0:
            wp, wn, wv = "REPUBLICAN", b["rep_candidate"] or "Republican Candidate", rep
        else:
            wp, wn, wv = "TIE", "Tie", max(dem, rep)

        results[county] = {
            "dem_candidate": b["dem_candidate"],
            "rep_candidate": b["rep_candidate"],
            "dem_votes": dem,
            "rep_votes": rep,
            "other_votes": other,
            "total_votes": total,
            "two_party_total": two_party,
            "margin": margin_abs,
            "margin_pct": margin_label(margin_signed, total),
            "winner": wp,
            "winner_name": wn,
            "winner_party": wp,
            "winner_incumbent": False,
            "winner_votes": wv,
            "competitiveness": competitiveness(margin_pct_num, wp),
            "all_parties": dict(b["party_votes"]),
            "candidates": b["candidates"],
            "contest": contest_name,
            "county": county,
            "year": year,
        }

    return {
        "contest_name": contest_name,
        "date": f"{year}0101",
        "state": "AL",
        "results": results,
    }


def year_from_president_csv_name(name: str) -> int | None:
    n = name.lower()
    if "table" in n:
        return None
    # Prefer explicit year at the end of the filename segment.
    m_end4 = re.search(r"[-_](19\d{2}|20\d{2})\.csv$", n)
    if m_end4:
        return int(m_end4.group(1))
    m2 = re.search(r"pres\.(\d{2})(?:_\d+)?\.csv$", n)
    if m2:
        yy = int(m2.group(1))
        return 2000 + yy if yy <= 30 else 1900 + yy
    # Fallback to the last 4-digit year token in filename.
    m4_all = re.findall(r"(19\d{2}|20\d{2})", n)
    if m4_all:
        return int(m4_all[-1])
    return None


def load_president_rows_from_csvs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(PRESIDENT_CSV_DIR.glob("eapresidentgeneral1976-2012_0-*.csv")):
        year = year_from_president_csv_name(p.name)
        if not year or not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        try:
            df = pd.read_csv(p, dtype=str).fillna("")
        except Exception:
            continue
        need = {"county", "party", "candidate", "votes"}
        if not need.issubset(df.columns):
            continue
        for _, r in df.iterrows():
            county = canonical_county(str(r["county"]))
            if not county:
                continue
            candidate_raw = str(r["candidate"]).strip()
            party_code_raw = str(r["party"]).strip().upper()
            candidate, party_code = split_candidate_and_party(candidate_raw, party_code_raw)
            if is_aggregate_candidate(candidate):
                continue
            votes = parse_int(r["votes"])
            if votes is None or votes <= 0:
                continue
            # Skip aggregate rows like "President" with blank party.
            if candidate.upper() in {"PRESIDENT", "TOTAL", "TOTALS"} and not party_code:
                continue
            rows.append(
                {
                    "year": str(year),
                    "contest_key": "president",
                    "contest_name": "President",
                    "county": county,
                    "party": party_name(party_code, candidate),
                    "candidate": "Write-ins" if candidate.upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"} else candidate,
                    "votes": votes,
                }
            )
    return rows


def load_president_rows_from_office_csvs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(PRESIDENT_OFFICE_CSV_DIR.glob("*__al__general__county__president*.csv")):
        m = re.match(r"^(\d{8})__al__general__county__president(?:__\d+)?\.csv$", p.name)
        if not m:
            continue
        year = int(m.group(1)[:4])
        if not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        try:
            df = pd.read_csv(p, dtype=str).fillna("")
        except Exception:
            continue
        need = {"county", "party", "candidate", "votes"}
        if not need.issubset(df.columns):
            continue
        for _, r in df.iterrows():
            county = canonical_county(str(r["county"]))
            if not county:
                continue
            candidate_raw = str(r["candidate"]).strip()
            party_code_raw = str(r["party"]).strip().upper()
            candidate, party_code = split_candidate_and_party(candidate_raw, party_code_raw)
            if is_excluded_president_candidate(str(year), candidate):
                continue
            if is_aggregate_candidate(candidate):
                continue
            votes = parse_int(r["votes"])
            if votes is None or votes <= 0:
                continue
            rows.append(
                {
                    "year": str(year),
                    "contest_key": "president",
                    "contest_name": "President",
                    "county": county,
                    "party": party_name(party_code, candidate),
                    "candidate": "Write-ins" if candidate.upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"} else candidate,
                    "votes": votes,
                }
            )
    return rows


def load_ussenate_rows_from_csvs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(US_SENATE_CSV_DIR.glob("*__al__general__county__ussenate*.csv")):
        m = re.match(r"^(\d{8})__al__general__county__ussenate(?:__\d+)?\.csv$", p.name)
        if not m:
            continue
        year = int(m.group(1)[:4])
        if not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        try:
            df = pd.read_csv(p, dtype=str).fillna("")
        except Exception:
            continue
        need = {"county", "party", "candidate", "votes"}
        if not need.issubset(df.columns):
            continue
        for _, r in df.iterrows():
            county = canonical_county(str(r["county"]))
            if not county:
                continue
            candidate_raw = str(r["candidate"]).strip()
            party_code_raw = str(r["party"]).strip().upper()
            candidate, party_code = split_candidate_and_party(candidate_raw, party_code_raw)
            if is_aggregate_candidate(candidate):
                continue
            votes = parse_int(r["votes"])
            if votes is None or votes <= 0:
                continue
            rows.append(
                {
                    "year": str(year),
                    "contest_key": "us_senate",
                    "contest_name": "U.S. Senate",
                    "county": county,
                    "party": party_name(party_code, candidate),
                    "candidate": "Write-ins" if candidate.upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"} else candidate,
                    "votes": votes,
                }
            )
    return rows


OFFICE_SLUG_TO_CONTEST = {
    "governor": ("governor", "Governor"),
    "ltgovernor": ("lieutenant_governor", "Lieutenant Governor"),
    "attorneygeneral": ("attorney_general", "Attorney General"),
    "secretaryofstate": ("secretary_of_state", "Secretary of State"),
    "treasurer": ("state_treasurer", "State Treasurer"),
    "auditor": ("state_auditor", "State Auditor"),
    "commissionerag": ("commissioner_of_agriculture", "Commissioner of Agriculture"),
    "commofagricultureindustries": ("commissioner_of_agriculture", "Commissioner of Agriculture"),
    "publicservicecommission": ("public_service_commissioner", "Public Service Commissioner"),
}


def load_statewide_rows_from_office_csvs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in sorted(US_SENATE_CSV_DIR.glob("*__al__general__county__*.csv")):
        m = re.match(r"^(\d{8})__al__general__county__([a-z0-9_]+)(?:__\d+)?\.csv$", p.name)
        if not m:
            continue
        year = int(m.group(1)[:4])
        if not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        office_slug = m.group(2).lower()
        if office_slug not in OFFICE_SLUG_TO_CONTEST:
            continue
        contest_key, contest_name = OFFICE_SLUG_TO_CONTEST[office_slug]

        try:
            df = pd.read_csv(p, dtype=str).fillna("")
        except Exception:
            continue
        need = {"county", "party", "candidate", "votes"}
        if not need.issubset(df.columns):
            continue

        for _, r in df.iterrows():
            county = canonical_county(str(r["county"]))
            if not county:
                continue
            candidate_raw = str(r["candidate"]).strip()
            party_code_raw = str(r["party"]).strip().upper()
            candidate, party_code = split_candidate_and_party(candidate_raw, party_code_raw)
            if is_aggregate_candidate(candidate):
                continue
            votes = parse_int(r["votes"])
            if votes is None or votes <= 0:
                continue
            rows.append(
                {
                    "year": str(year),
                    "contest_key": contest_key,
                    "contest_name": contest_name,
                    "county": county,
                    "party": party_name(party_code, candidate),
                    "candidate": "Write-ins" if candidate.upper() in {"WRITE-IN", "WRITE INS", "WRITE-INS"} else candidate,
                    "votes": votes,
                }
            )
    return rows


def main() -> None:
    base = json.loads(BASE_JSON.read_text(encoding="utf-8"))
    ry = base.get("results_by_year", {})

    # Start with existing statewide + us_senate from base JSON in requested window.
    merged: dict[str, dict[str, Any]] = {}
    for y, contests in ry.items():
        try:
            yi = int(y)
        except ValueError:
            continue
        if yi < YEAR_MIN or yi > YEAR_MAX:
            continue
        out_c = {}
        for ck, payload in contests.items():
            lk = ck.lower()
            if lk.startswith("president_") or lk.startswith("us_senate_") or lk.startswith("governor_") or lk.startswith("lieutenant_governor_") or lk.startswith("attorney_general_") or lk.startswith("secretary_of_state_") or lk.startswith("state_treasurer_") or lk.startswith("state_auditor_") or lk.startswith("commissioner_of_agriculture_") or lk.startswith("public_service_commissioner_"):
                contest_base = re.sub(r"_\d{4}$", "", ck)
                out_c[ck] = normalize_contest_payload_names(payload, y, contest_base)
        if out_c:
            merged[y] = out_c

    # Parse recursive precinct workbooks and overlay contests from these files.
    workbook_paths = sorted(DATA_DIR.rglob("*.xls")) + sorted(DATA_DIR.rglob("*.xlsx"))
    all_rows: list[dict[str, Any]] = []
    parsed_files = 0
    for p in workbook_paths:
        rows = parse_precinct_workbook(p)
        if rows:
            all_rows.extend(rows)
            parsed_files += 1

    # Backfill president from county-level president CSV extracts (1976+ sources).
    all_rows.extend(load_president_rows_from_csvs())
    # NOTE: load_president_rows_from_office_csvs() is intentionally NOT called here.
    # The openelections_office_normalized_2016_2024 directory is an *output* of the
    # export script (export_2016_2024_openelections_normalized.py), so reading it back
    # in would create a circular dependency and double-count XLS-derived vote totals.
    # Presidential data for 2016/2020/2024 is fully covered by the XLS workbooks.
    # Backfill U.S. Senate county general-election CSV extracts.
    all_rows.extend(load_ussenate_rows_from_csvs())
    # Backfill statewide offices from normalized county general-election CSV extracts.
    all_rows.extend(load_statewide_rows_from_office_csvs())

    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    seen_rows: set[tuple[str, str, str, str, str, str, int]] = set()
    for r in all_rows:
        if str(r.get("contest_key", "")) == "president" and is_excluded_president_candidate(
            str(r.get("year", "")), str(r.get("candidate", ""))
        ):
            continue
        county = canonical_county(r.get("county", ""))
        if not county:
            continue
        row_sig = (
            str(r["year"]),
            str(r["contest_key"]),
            str(r["contest_name"]),
            county,
            str(r["party"]).upper().strip(),
            normalize_candidate_name(str(r["candidate"])),
            int(r["votes"]),
        )
        if row_sig in seen_rows:
            continue
        seen_rows.add(row_sig)
        r["county"] = county
        r["candidate"] = normalize_candidate_name(str(r["candidate"]))
        r["party"] = str(r["party"]).upper().strip()
        by_key[(r["year"], r["contest_key"], r["contest_name"])].append(r)

    overlaid = 0
    for (year, ckey, cname), rows in by_key.items():
        yi = int(year)
        if ckey == "president" and (yi < 1968 or yi % 4 != 0):
            continue
        payload = build_payload(rows, year, ckey, cname)
        result_count = len(payload.get("results", {}))
        # Skip partial presidential overlays; they usually indicate incomplete source files.
        if ckey == "president" and result_count < 67:
            print(f"Skipping incomplete presidential overlay {year}: {result_count} counties")
            continue
        full_key = f"{ckey}_{year}"
        merged.setdefault(year, {})
        merged[year][full_key] = normalize_contest_payload_names(payload, year, ckey)
        overlaid += 1

    # Drop empty contest payloads (e.g., placeholder years with no county results).
    pruned: dict[str, dict[str, Any]] = {}
    for y, contests in merged.items():
        kept: dict[str, Any] = {}
        for ck, payload in contests.items():
            results = payload.get("results", {}) if isinstance(payload, dict) else {}
            if isinstance(results, dict) and len(results) > 0:
                kept[ck] = payload
        if kept:
            pruned[y] = kept

    final_out = {"results_by_year": {y: dict(sorted(c.items())) for y, c in sorted(pruned.items(), key=lambda kv: int(kv[0]))}}
    OUTPUT_JSON.write_text(json.dumps(final_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {OUTPUT_JSON}")
    print(f"Base years kept: {len(merged)}")
    print(f"Precinct files parsed: {parsed_files}")
    print(f"Contest-year overlays from precinct files: {overlaid}")
    print(f"Total contests in output: {sum(len(v) for v in final_out['results_by_year'].values())}")


if __name__ == "__main__":
    main()
