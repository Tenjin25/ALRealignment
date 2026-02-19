from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


INPUT_DIR = Path("data/openelections_office_normalized")
OUTPUT_PATHS = [Path("results_by_year_grouped.final.json"), Path("data/results_by_year_grouped.final.json")]

PARTY_CODE_TO_NAME = {
    "DEM": "DEMOCRAT",
    "REP": "REPUBLICAN",
    "LIB": "LIBERTARIAN",
    "IND": "INDEPENDENT",
    "NON": "NONPARTISAN",
}


def contest_key_for_office_slug(slug: str) -> str:
    mapping = {
        "president": "president",
        "ussenate": "us_senate",
        "governor": "governor",
        "ltgovernor": "lieutenant_governor",
        "attorneygeneral": "attorney_general",
        "secretaryofstate": "secretary_of_state",
        "treasurer": "state_treasurer",
        "auditor": "state_auditor",
        "commissionerag": "commissioner_of_agriculture",
    }
    return mapping.get(slug, slug)


def parse_int_votes(v: object) -> int | None:
    s = str(v).strip()
    if not s or not re.fullmatch(r"-?\d+(\.\d+)?", s):
        return None
    f = float(s)
    if not f.is_integer():
        return None
    return int(f)


def canonical_county(name: str) -> str:
    s = str(name).strip()
    if not s:
        return ""
    if s.lower() in {"total", "margin", "state total"}:
        return ""
    return s.title()


def normalize_party_name(code: str) -> str:
    c = str(code).strip().upper()
    return PARTY_CODE_TO_NAME.get(c, c if c else "OTHER")


def normalize_candidate_name(name: str) -> str:
    raw = str(name).strip()
    if not raw:
        return raw
    if "," in raw:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if len(parts) >= 2:
            raw = " ".join(parts[1:] + [parts[0]])
    letters = [ch for ch in raw if ch.isalpha()]
    if letters and all(ch.isupper() for ch in letters):
        raw = raw.title()
    return re.sub(r"\s+", " ", raw).strip()


def competitiveness(margin_pct: float, winner_party: str) -> dict[str, str]:
    if winner_party not in {"DEMOCRAT", "REPUBLICAN"}:
        return {"category": "Tossup", "party": "TIE", "code": "TOSSUP", "color": "#f7f7f7"}

    if margin_pct >= 40:
        cat = "Annihilation"
        color = "#08306b" if winner_party == "DEMOCRAT" else "#67000d"
    elif margin_pct >= 30:
        cat = "Dominant"
        color = "#08519c" if winner_party == "DEMOCRAT" else "#a50f15"
    elif margin_pct >= 20:
        cat = "Stronghold"
        color = "#3182bd" if winner_party == "DEMOCRAT" else "#cb181d"
    elif margin_pct >= 10:
        cat = "Safe"
        color = "#6baed6" if winner_party == "DEMOCRAT" else "#ef3b2c"
    elif margin_pct >= 5.5:
        cat = "Likely"
        color = "#9ecae1" if winner_party == "DEMOCRAT" else "#fb6a4a"
    elif margin_pct >= 1:
        cat = "Lean"
        color = "#c6dbef" if winner_party == "DEMOCRAT" else "#fcae91"
    elif margin_pct >= 0.5:
        cat = "Tilt"
        color = "#e1f5fe" if winner_party == "DEMOCRAT" else "#fee8c8"
    else:
        return {"category": "Tossup", "party": winner_party, "code": f"{winner_party}_TOSSUP", "color": "#f7f7f7"}
    return {"category": cat, "party": winner_party, "code": f"{winner_party}_{cat.upper()}", "color": color}


def margin_pct_label(margin: int, total_votes: int) -> str:
    if total_votes <= 0:
        return "TIE+0.00"
    pct = abs(margin) / total_votes * 100.0
    if margin > 0:
        return f"D+{pct:.2f}"
    if margin < 0:
        return f"R+{pct:.2f}"
    return "TIE+0.00"


def build_for_file(path: Path) -> tuple[str, str, dict] | None:
    m = re.match(r"^(\d{8})__al__general__county__([a-z0-9]+)(?:__\d+)?\.csv$", path.name)
    if not m:
        return None
    ymd = m.group(1)
    year = ymd[:4]
    office_slug = m.group(2)
    contest_key_base = contest_key_for_office_slug(office_slug)
    contest_key = f"{contest_key_base}_{year}"

    df = pd.read_csv(path, dtype=str).fillna("")
    required = {"county", "party", "candidate", "votes", "office"}
    if not required.issubset(df.columns):
        return None

    county_bins: dict[str, dict] = {}
    office_label = str(df["office"].iloc[0]).strip() or contest_key_base.replace("_", " ").title()

    for _, row in df.iterrows():
        county = canonical_county(row["county"])
        if not county:
            continue

        candidate = normalize_candidate_name(str(row["candidate"]).strip())
        party_code = str(row["party"]).strip().upper()
        votes = parse_int_votes(row["votes"])
        if votes is None:
            continue
        if candidate.lower() in {"total", "totals", "ballots cast", "total ballots cast"}:
            continue

        bucket = county_bins.setdefault(
            county,
            {
                "party_votes": {},
                "candidates": {},
                "dem_candidate": "",
                "rep_candidate": "",
            },
        )

        party_name = normalize_party_name(party_code)
        bucket["party_votes"][party_name] = bucket["party_votes"].get(party_name, 0) + votes
        if candidate not in bucket["candidates"]:
            bucket["candidates"][candidate] = {"votes": 0, "party": party_name, "incumbent": False}
        bucket["candidates"][candidate]["votes"] += votes

        if party_name == "DEMOCRAT" and not bucket["dem_candidate"]:
            bucket["dem_candidate"] = candidate
        if party_name == "REPUBLICAN" and not bucket["rep_candidate"]:
            bucket["rep_candidate"] = candidate

    results: dict[str, dict] = {}
    for county, b in county_bins.items():
        dem_votes = int(b["party_votes"].get("DEMOCRAT", 0))
        rep_votes = int(b["party_votes"].get("REPUBLICAN", 0))
        total_votes = int(sum(b["party_votes"].values()))
        other_votes = int(total_votes - dem_votes - rep_votes)
        two_party_total = int(dem_votes + rep_votes)
        margin = int(dem_votes - rep_votes)
        margin_pct_num = (abs(margin) / total_votes * 100.0) if total_votes > 0 else 0.0

        if margin > 0:
            winner_party = "DEMOCRAT"
            winner_name = b["dem_candidate"] or "Democratic Candidate"
            winner_votes = dem_votes
        elif margin < 0:
            winner_party = "REPUBLICAN"
            winner_name = b["rep_candidate"] or "Republican Candidate"
            winner_votes = rep_votes
        else:
            winner_party = "TIE"
            winner_name = "Tie"
            winner_votes = max(dem_votes, rep_votes)

        results[county] = {
            "dem_candidate": b["dem_candidate"],
            "rep_candidate": b["rep_candidate"],
            "dem_votes": dem_votes,
            "rep_votes": rep_votes,
            "other_votes": other_votes,
            "total_votes": total_votes,
            "two_party_total": two_party_total,
            "margin": abs(margin),
            "margin_pct": margin_pct_label(margin, total_votes),
            "winner": winner_party,
            "winner_name": winner_name,
            "winner_party": winner_party,
            "winner_incumbent": False,
            "winner_votes": winner_votes,
            "competitiveness": competitiveness(margin_pct_num, winner_party),
            "all_parties": b["party_votes"],
            "candidates": b["candidates"],
            "contest": office_label,
            "county": county,
            "year": year,
        }

    payload = {"contest_name": office_label, "date": ymd, "state": "AL", "results": results}
    return year, contest_key, payload


def main() -> None:
    results_by_year: dict[str, dict] = {}
    files = sorted(INPUT_DIR.glob("*__al__general__county__*.csv"))
    built = 0

    for path in files:
        parsed = build_for_file(path)
        if not parsed:
            continue
        year, contest_key, payload = parsed
        results_by_year.setdefault(year, {})
        if contest_key in results_by_year[year]:
            continue
        results_by_year[year][contest_key] = payload
        built += 1

    out = {"results_by_year": dict(sorted(results_by_year.items(), key=lambda x: x[0]))}
    serialized = json.dumps(out, indent=2, ensure_ascii=False)
    for op in OUTPUT_PATHS:
        op.write_text(serialized, encoding="utf-8")
    print(f"Wrote {built} contests across {len(results_by_year)} years.")
    for op in OUTPUT_PATHS:
        print(f"- {op}")


if __name__ == "__main__":
    main()
