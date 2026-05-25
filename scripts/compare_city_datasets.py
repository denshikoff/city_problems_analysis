"""Сравнительная статистика по датасетам Воронежа и Санкт-Петербурга.

Запуск из корня проекта:
python scripts/compare_city_datasets.py \
  --voronezh data/data_voronesh.xlsx \
  --spb data/data_spb.xlsx \
  --out outputs/city_comparison.json

Скрипт специально читает XLSX потоково через lxml, чтобы не держать весь файл в памяти.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import statistics
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable
from lxml import etree

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    shared: list[str] = []
    with zf.open("xl/sharedStrings.xml") as fh:
        for _, si in etree.iterparse(fh, events=("end",), tag=NS + "si"):
            shared.append("".join(si.itertext()))
            si.clear()
            while si.getprevious() is not None:
                del si.getparent()[0]
    return shared


def _column_index(cell_ref: str | None) -> int:
    match = re.match(r"([A-Z]+)", cell_ref or "")
    value = 0
    for char in match.group(1) if match else "":
        value = value * 26 + ord(char) - 64
    return value - 1


def _cell_value(cell, shared: list[str]) -> str:
    value = cell.find(NS + "v")
    if value is None or value.text is None:
        return ""
    return shared[int(value.text)] if cell.get("t") == "s" else value.text


def iter_xlsx_rows(path: Path, sheet_xml: str = "xl/worksheets/sheet1.xml") -> Iterable[dict[int, str]]:
    with zipfile.ZipFile(path) as zf:
        shared = _load_shared_strings(zf)
        with zf.open(sheet_xml) as fh:
            for _, row in etree.iterparse(fh, events=("end",), tag=NS + "row"):
                values: dict[int, str] = {}
                for cell in row.iterchildren(tag=NS + "c"):
                    values[_column_index(cell.get("r"))] = _cell_value(cell, shared)
                yield values
                row.clear()
                while row.getprevious() is not None:
                    del row.getparent()[0]


def parse_date(value: object) -> dt.date | None:
    text = str(value or "").strip()
    try:
        number = float(text)
        if 20000 < number < 80000:
            return (dt.datetime(1899, 12, 30) + dt.timedelta(days=number)).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(text[:19], fmt).date()
        except ValueError:
            pass
    return None


def summarize(path: Path, city: str, schema: str) -> dict:
    if schema == "voronezh":
        columns = {"date": 11, "direction": 13, "topic": 14, "municipality": 15, "locality": 16, "street": 17, "house": 18, "object": 20, "text": 24}
    else:
        columns = {"date": 0, "direction": 3, "topic": 4, "location": 6, "text": 8}

    rows = iter_xlsx_rows(path)
    next(rows, None)  # header
    directions: Counter[str] = Counter()
    topics: Counter[str] = Counter()
    locations: Counter[str] = Counter()
    months: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()
    lengths: list[int] = []
    date_min: dt.date | None = None
    date_max: dt.date | None = None
    total = 0

    for row in rows:
        total += 1
        direction = (row.get(columns["direction"]) or "Без направления").strip()
        topic = (row.get(columns["topic"]) or "Без темы").strip()
        if schema == "voronezh":
            location = ", ".join(
                row.get(columns[key], "").strip()
                for key in ("municipality", "locality", "street", "house", "object")
                if row.get(columns[key], "").strip()
            ) or "Не указано"
        else:
            location = (row.get(columns["location"]) or "Не указано").strip() or "Не указано"
        current_date = parse_date(row.get(columns["date"]))
        if current_date:
            date_min = current_date if date_min is None or current_date < date_min else date_min
            date_max = current_date if date_max is None or current_date > date_max else date_max
            months[current_date.strftime("%Y-%m")] += 1
        text = row.get(columns["text"], "")
        lengths.append(len(text))
        directions[direction] += 1
        topics[topic] += 1
        locations[location] += 1
        pairs[(direction, topic)] += 1

    return {
        "city": city,
        "appeals": total,
        "date_min": date_min.isoformat() if date_min else None,
        "date_max": date_max.isoformat() if date_max else None,
        "directions_count": len(directions),
        "topics_count": len(topics),
        "problem_groups_ge5": sum(1 for value in pairs.values() if value >= 5),
        "mean_text_length": round(statistics.mean(lengths), 1) if lengths else 0,
        "median_text_length": statistics.median(lengths) if lengths else 0,
        "top_directions": directions.most_common(20),
        "top_topics": topics.most_common(20),
        "top_locations": locations.most_common(20),
        "monthly": sorted(months.items()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voronezh", type=Path, required=True)
    parser.add_argument("--spb", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/city_comparison.json"))
    args = parser.parse_args()

    result = {
        "method": "problem group = pair(direction, topic/category), threshold >= 5 appeals",
        "cities": [
            summarize(args.voronezh, "Воронеж", "voronezh"),
            summarize(args.spb, "Санкт-Петербург", "spb"),
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
