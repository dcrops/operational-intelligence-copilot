"""
Generate a synthetic workforce dataset for the Operational Intelligence Copilot demo.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

TOTAL_RECORDS = 250
OUTPUT_PATH = Path("data/sample/workforce_demo_v2.csv")

MONTHS = [
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
]
DEPARTMENTS = ["Ops", "Finance", "HR", "Sales", "IT"]
LOCATIONS = ["Melbourne", "Sydney", "Brisbane"]
MANAGERS = ["Sarah", "Michael", "Priya", "James"]
EMPLOYMENT_TYPES = ["Full Time", "Part Time", "Contract"]

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Casey", "Morgan", "Riley", "Avery", "Quinn",
    "Sam", "Jamie", "Blake", "Drew", "Hayden", "Logan", "Reese", "Skyler",
    "Cameron", "Parker", "Sydney", "Rowan", "Elliot", "Finley", "Harper",
    "Jesse", "Kai", "Lane", "Marley", "Noel", "Oakley", "Peyton", "River",
    "Shawn", "Toby", "Uma", "Val", "Winter", "Xander", "Yael", "Zion",
    "Amelia", "Ben", "Chloe", "Daniel", "Ella", "Felix", "Grace", "Hugo",
    "Isla", "Jack",
]
LAST_NAMES = [
    "Nguyen", "Patel", "Smith", "Brown", "Wilson", "Lee", "Martin", "Clark",
    "Lewis", "Walker", "Hall", "Young", "King", "Wright", "Scott", "Green",
    "Baker", "Adams", "Campbell", "Turner", "Phillips", "Evans", "Edwards",
    "Collins", "Stewart", "Morris", "Rogers", "Reed", "Cook", "Bell", "Bailey",
    "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres", "Peterson",
    "Gray", "Ramirez", "James", "Watson", "Brooks", "Kelly", "Sanders", "Price",
    "Bennett", "Wood", "Barnes", "Ross",
]

COLUMNS = [
    "employee_id",
    "employee_name",
    "department",
    "month",
    "hours",
    "overtime_hours",
    "absence_days",
    "location",
    "manager",
    "employment_type",
]

ANOMALY_COUNT = 5
HIGH_OVERTIME_COUNT = 5
HIGH_ABSENCE_COUNT = 5

RANDOM_SEED = 42


def _hours_for_department(department: str, month_index: int) -> float:
    """Return monthly hours with trend and variance baked in."""
    if department == "Ops":
        # Gradual increase from January through May.
        base = 180 + (month_index * 12)
        return round(random.uniform(base, base + 8), 1)

    if department == "Finance":
        # Lowest overall hours.
        return round(random.uniform(140, 150), 1)

    return round(random.uniform(140, 158), 1)


def _normal_overtime_hours() -> float:
    return round(random.uniform(0, 15), 1)


def _normal_absence_days() -> int:
    return random.randint(0, 2)


def _build_base_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    employees_per_department = TOTAL_RECORDS // (len(DEPARTMENTS) * len(MONTHS))

    employee_counter = 1
    for department in DEPARTMENTS:
        for _employee_index in range(employees_per_department):
            employee_id = f"E{employee_counter:04d}"
            first_name = FIRST_NAMES[(employee_counter - 1) % len(FIRST_NAMES)]
            last_name = LAST_NAMES[(employee_counter - 1) % len(LAST_NAMES)]
            employee_name = f"{first_name} {last_name}"

            for month_index, month in enumerate(MONTHS):
                records.append(
                    {
                        "employee_id": employee_id,
                        "employee_name": employee_name,
                        "department": department,
                        "month": month,
                        "hours": _hours_for_department(department, month_index),
                        "overtime_hours": _normal_overtime_hours(),
                        "absence_days": _normal_absence_days(),
                        "location": random.choice(LOCATIONS),
                        "manager": random.choice(MANAGERS),
                        "employment_type": random.choice(EMPLOYMENT_TYPES),
                    }
                )

            employee_counter += 1

    return records


def _inject_scenarios(records: list[dict[str, object]]) -> None:
    rng = random.Random(RANDOM_SEED)

    # Keep hour anomalies out of Ops and Finance to preserve trend and variance storylines.
    anomaly_plan = [("HR", 2), ("Sales", 2), ("IT", 1)]
    anomaly_indices: list[int] = []
    for department, count in anomaly_plan:
        candidates = [
            index
            for index, record in enumerate(records)
            if record["department"] == department
        ]
        anomaly_indices.extend(rng.sample(candidates, count))
    for index in anomaly_indices:
        records[index]["hours"] = round(random.uniform(600, 1000), 1)

    remaining_indices = [i for i in range(len(records)) if i not in anomaly_indices]
    overtime_indices = rng.sample(remaining_indices, HIGH_OVERTIME_COUNT)
    for index in overtime_indices:
        records[index]["overtime_hours"] = round(random.uniform(50.5, 80), 1)

    remaining_indices = [i for i in remaining_indices if i not in overtime_indices]
    absence_indices = rng.sample(remaining_indices, HIGH_ABSENCE_COUNT)
    for index in absence_indices:
        records[index]["absence_days"] = random.randint(10, 15)


def _summary_counts(records: list[dict[str, object]]) -> tuple[int, int, int]:
    anomaly_count = sum(
        1 for record in records if 600 <= float(record["hours"]) <= 1000
    )
    high_overtime_count = sum(
        1 for record in records if float(record["overtime_hours"]) > 50
    )
    high_absence_count = sum(
        1 for record in records if int(record["absence_days"]) >= 10
    )
    return anomaly_count, high_overtime_count, high_absence_count


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

    anomaly_count, high_overtime_count, high_absence_count = _summary_counts(records)

    print(f"total records generated: {len(records)}")
    print(f"anomaly count: {anomaly_count}")
    print(f"high overtime count: {high_overtime_count}")
    print(f"high absence count: {high_absence_count}")
    print(f"saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
