from __future__ import annotations

import argparse
import calendar
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def first_tuesday_after_first_monday(year: int, month: int) -> date:
    d = date(year, month, 1)
    while d.weekday() != calendar.MONDAY:
        d += timedelta(days=1)
    return d + timedelta(days=1)


def parse_year(stem: str) -> int | None:
    m8 = re.match(r"^(\d{4})\d{4}__", stem)
    if m8:
        return int(m8.group(1))

    s = stem.lower()

    marker_matches = re.findall(r"(?:gen|pri|pres|runoff|ro)[^0-9]*(\d{2,4})", s)
    if marker_matches:
        num = marker_matches[-1]
        if len(num) == 4:
            return int(num)
        yy = int(num)
        return 2000 + yy if yy <= 30 else 1900 + yy

    tokens = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    for token in reversed(tokens):
        if re.fullmatch(r"\d{4}", token):
            return int(token)
        if re.fullmatch(r"\d{2}", token):
            yy = int(token)
            return 2000 + yy if yy <= 30 else 1900 + yy

    m4 = re.findall(r"(19\d{2}|20\d{2})", s)
    if m4:
        return int(m4[0])
    return None


def parse_election_slug(stem: str) -> str:
    s = stem.lower()
    tokens = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    token_set = set(tokens)

    is_runoff = (
        "runoff" in token_set
        or "ro" in token_set
        or bool(re.search(r"ro\d{2,4}", s))
    )
    is_primary = "pri" in token_set or "primary" in token_set
    is_general = (
        "gen" in token_set
        or "general" in token_set
        or "pres" in token_set
        or "generalelection" in s
    )

    party = ""
    if "dem" in token_set:
        party = "democratic"
    elif "rep" in token_set:
        party = "republican"

    if is_general:
        return "general"
    if is_primary and is_runoff:
        return f"{party + '-' if party else ''}primary-runoff"
    if is_primary:
        return f"{party + '-' if party else ''}primary"
    if is_runoff:
        return f"{party + '-' if party else ''}runoff"
    return "election"


def infer_scope(csv_path: Path) -> str:
    try:
        df = pd.read_csv(csv_path, usecols=["precinct"], nrows=2000, dtype=str)
    except Exception:
        return "county"
    has_precinct = df["precinct"].fillna("").str.strip().ne("").any()
    return "precinct" if has_precinct else "county"


def build_date(year: int, election_slug: str) -> str:
    if election_slug == "general":
        return first_tuesday_after_first_monday(year, 11).strftime("%Y%m%d")
    if "primary-runoff" in election_slug:
        d = first_tuesday_after_first_monday(year, 6) + timedelta(days=21)
        return d.strftime("%Y%m%d")
    if "primary" in election_slug:
        return first_tuesday_after_first_monday(year, 6).strftime("%Y%m%d")
    if "runoff" in election_slug:
        d = first_tuesday_after_first_monday(year, 6) + timedelta(days=21)
        return d.strftime("%Y%m%d")
    return f"{year}0101"


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize OpenElections filenames.")
    parser.add_argument("--input-dir", default="data/openelections")
    parser.add_argument("--output-dir", default="data/openelections_canonical")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for existing in out_dir.glob("*.csv"):
        existing.unlink()

    rows: list[dict[str, str]] = []
    used_names: set[str] = set()

    for csv_path in sorted(in_dir.glob("*.csv")):
        if csv_path.name == "_conversion_summary.csv":
            continue

        stem = csv_path.stem
        if re.match(r"^\d{8}__al__[-a-z0-9]+__(?:county|precinct)(?:__[-a-z0-9]+)?$", stem):
            target_name = csv_path.name
        else:
            year = parse_year(stem)
            if year is None:
                year = 1900
            election_slug = parse_election_slug(stem)
            scope = infer_scope(csv_path)
            source_slug = slugify(stem)
            ymd = build_date(year, election_slug)
            target_name = f"{ymd}__al__{election_slug}__{scope}__{source_slug}.csv"

        base_name = target_name
        i = 2
        while target_name in used_names:
            target_name = base_name.replace(".csv", f"__{i}.csv")
            i += 1
        used_names.add(target_name)

        target = out_dir / target_name
        content = csv_path.read_text(encoding="utf-8", errors="ignore")
        target.write_text(content, encoding="utf-8", newline="")
        rows.append({"source": csv_path.name, "canonical": target_name})

    mapping = out_dir / "_filename_mapping.csv"
    pd.DataFrame(rows).to_csv(mapping, index=False)
    print(f"Wrote {len(rows)} canonical file(s) to {out_dir}")
    print(f"Mapping: {mapping}")


if __name__ == "__main__":
    main()
