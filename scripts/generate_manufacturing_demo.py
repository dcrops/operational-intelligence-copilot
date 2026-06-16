"""
Generate a synthetic manufacturing dataset for the Operational Intelligence Copilot demo.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

TOTAL_RECORDS = 300
OUTPUT_PATH = Path("data/sample/manufacturing_demo.csv")
RANDOM_SEED = 42

MONTHS = [
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
    "2026-06-01",
]
PRODUCTION_LINES = ["Line A", "Line B", "Line C", "Line D", "Line E"]
SHIFTS = ["Day", "Night", "Swing"]
SITES = ["North Plant", "South Plant", "East Plant"]
SUPERVISORS = [
    "Taylor",
    "Morgan",
    "Casey",
    "Jordan",
    "Riley",
    "Alex",
    "Sam",
    "Jamie",
    "Blake",
    "Drew",
]

COLUMNS = [
    "month",
    "production_line",
    "shift",
    "defects",
    "downtime_minutes",
    "units_produced",
    "site",
    "supervisor",
]

HIGH_DEFECT_COUNT = 5
HIGH_DOWNTIME_COUNT = 5
HIGH_DEFECT_MIN = 45
HIGH_DEFECT_MAX = 80
HIGH_DOWNTIME_MIN = 120
HIGH_DOWNTIME_MAX = 200


def _normal_defects(production_line: str) -> int:
    if production_line in {"Line A", "Line B"}:
        return random.randint(2, 5)
    if production_line == "Line C":
        return random.randint(12, 18)
    return random.randint(5, 10)


def _normal_downtime(month_index: int) -> int:
    base = 18 + (month_index * 7)
    return random.randint(base, base + 12)


def _normal_units_produced(production_line: str) -> int:
    if production_line in {"Line A", "Line B"}:
        return random.randint(950, 1100)
    return random.randint(780, 1050)


def _build_base_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    combos_per_line = TOTAL_RECORDS // (len(PRODUCTION_LINES) * len(MONTHS))

    for production_line in PRODUCTION_LINES:
        for combo_index in range(combos_per_line):
            shift = SHIFTS[combo_index % len(SHIFTS)]
            site = SITES[combo_index % len(SITES)]
            supervisor = SUPERVISORS[combo_index % len(SUPERVISORS)]

            for month_index, month in enumerate(MONTHS):
                records.append(
                    {
                        "month": month,
                        "production_line": production_line,
                        "shift": shift,
                        "defects": _normal_defects(production_line),
                        "downtime_minutes": _normal_downtime(month_index),
                        "units_produced": _normal_units_produced(production_line),
                        "site": site,
                        "supervisor": supervisor,
                    }
                )

    return records


def _inject_scenarios(records: list[dict[str, object]]) -> None:
    rng = random.Random(RANDOM_SEED)

    defect_candidates = [
        index
        for index, record in enumerate(records)
        if record["production_line"] not in {"Line A", "Line B"}
    ]
    defect_indices = rng.sample(defect_candidates, HIGH_DEFECT_COUNT)
    for index in defect_indices:
        records[index]["defects"] = random.randint(HIGH_DEFECT_MIN, HIGH_DEFECT_MAX)

    remaining_indices = [index for index in range(len(records)) if index not in defect_indices]
    downtime_indices = rng.sample(remaining_indices, HIGH_DOWNTIME_COUNT)
    for index in downtime_indices:
        records[index]["downtime_minutes"] = random.randint(
            HIGH_DOWNTIME_MIN,
            HIGH_DOWNTIME_MAX,
        )


def _summary(records: list[dict[str, object]]) -> None:
    defects_by_line: dict[str, int] = defaultdict(int)
    downtime_by_month: dict[str, int] = defaultdict(int)

    high_defect_count = 0
    high_downtime_count = 0

    for record in records:
        production_line = str(record["production_line"])
        month = str(record["month"])
        defects = int(record["defects"])
        downtime = int(record["downtime_minutes"])

        defects_by_line[production_line] += defects
        downtime_by_month[month] += downtime

        if HIGH_DEFECT_MIN <= defects <= HIGH_DEFECT_MAX:
            high_defect_count += 1
        if HIGH_DOWNTIME_MIN <= downtime <= HIGH_DOWNTIME_MAX:
            high_downtime_count += 1

    highest_defect_line = max(defects_by_line, key=defects_by_line.get)
    sorted_months = sorted(downtime_by_month.items(), key=lambda item: item[0])

    print(f"total rows: {len(records)}")
    print(f"high defect scenario count: {high_defect_count}")
    print(f"high downtime scenario count: {high_downtime_count}")
    print(f"highest total defects by production line: {highest_defect_line}")
    print(
        "downtime trend by month: "
        + ", ".join(f"{month}={total}" for month, total in sorted_months)
    )
    print("stable comparison lines: Line A and Line B remain low-defect baselines")
    print(f"saved to: {OUTPUT_PATH}")


def main() -> None:
    random.seed(RANDOM_SEED)

    records = _build_base_records()
    if len(records) != TOTAL_RECORDS:
        raise RuntimeError(f"Expected {TOTAL_RECORDS} records, generated {len(records)}")

    _inject_scenarios(records)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    _summary(records)


if __name__ == "__main__":
    main()
