from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


def office_to_slug(office: str) -> str:
    o = office.strip().lower()
    o = o.replace("u.s.", "us").replace("u. s.", "us")
    o = o.replace("associate justice, supreme court", "supremecourt")
    o = o.replace("court of civil appeals", "civilappeals")
    o = o.replace("court of criminal appeals", "criminalappeals")
    o = o.replace("lieutenant governor", "ltgovernor")
    o = o.replace("attorney general", "attorneygeneral")
    o = o.replace("secretary of state", "secretaryofstate")
    o = o.replace("state treasurer", "treasurer")
    o = o.replace("state auditor", "auditor")
    o = o.replace("commissioner of agriculture and industries", "commissionerag")
    o = o.replace("total ballots cast", "ballotscast")
    o = re.sub(r"[^a-z0-9]+", "", o)
    if o in {"ussenator", "ussenate", "unitedstatessenator"}:
        return "ussenate"
    if o in {"ushouse", "unitedstateshouse"}:
        return "ushouse"
    if o == "presidentoftheunitedstates":
        return "president"
    if not o:
        return "office"
    return o


def infer_office_slug(csv_path: Path) -> str:
    try:
        df = pd.read_csv(csv_path, usecols=["office"], dtype=str)
    except Exception:
        return "office"

    offices = sorted({str(x).strip() for x in df["office"].dropna().tolist() if str(x).strip()})
    if not offices:
        return "office"
    if len(offices) > 1:
        return "multioffice"
    return office_to_slug(offices[0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize office portion in canonical OpenElections filenames.")
    parser.add_argument("--input-dir", default="data/openelections_canonical")
    parser.add_argument("--output-dir", default="data/openelections_office_normalized")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("*.csv"):
        old.unlink()

    mapping_rows: list[dict[str, str]] = []
    used_names: set[str] = set()

    pat = re.compile(r"^(\d{8})__([a-z]{2})__([a-z0-9-]+)__(county|precinct)(?:__(.+))?$")

    for src in sorted(in_dir.glob("*.csv")):
        if src.name == "_filename_mapping.csv":
            continue

        m = pat.match(src.stem)
        if not m:
            target_name = src.name
        else:
            ymd, state, election, scope = m.group(1), m.group(2), m.group(3), m.group(4)
            office_slug = infer_office_slug(src)
            target_name = f"{ymd}__{state}__{election}__{scope}__{office_slug}.csv"

        base = target_name
        i = 2
        while target_name in used_names:
            target_name = base.replace(".csv", f"__{i}.csv")
            i += 1
        used_names.add(target_name)

        dst = out_dir / target_name
        dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8", newline="")
        mapping_rows.append({"source": src.name, "normalized": target_name})

    mapping_path = out_dir / "_office_filename_mapping.csv"
    pd.DataFrame(mapping_rows).to_csv(mapping_path, index=False)
    print(f"Wrote {len(mapping_rows)} file(s) to {out_dir}")
    print(f"Mapping: {mapping_path}")


if __name__ == "__main__":
    main()
