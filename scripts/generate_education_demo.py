"""
Generate a synthetic education dataset for the Operational Intelligence Copilot demo.
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

TOTAL_RECORDS = 300
OUTPUT_PATH = Path("data/sample/education_demo.csv")
RANDOM_SEED = 42

MONTHS = [
    "2026-01-01",
    "2026-02-01",
    "2026-03-01",
    "2026-04-01",
    "2026-05-01",
    "2026-06-01",
]
SCHOOLS = ["School A", "School B", "School C", "School D", "School E"]
CAMPUSES = ["Main", "West"]
YEAR_LEVELS = ["Year 7", "Year 8", "Year 9", "Year 10", "Year 11"]
PROGRAM_TYPES = ["Mainstream", "Extended", "Support"]

COLUMNS = [
    "month",
    "school",
    "year_level",
    "attendance_rate",
    "behaviour_incidents",
    "average_score",
    "campus",
    "program_type",
]

LOW_ATTENDANCE_COUNT = 5
HIGH_BEHAVIOUR_COUNT = 5
LOW_ATTENDANCE_MIN = 45.0
LOW_ATTENDANCE_MAX = 60.0
HIGH_BEHAVIOUR_MIN = 25
HIGH_BEHAVIOUR_MAX = 40


def _attendance_rate(school: str, month_index: int) -> float:
    if school == "School C":
        start = 92.0
        end = 75.0
        step = (start - end) / (len(MONTHS) - 1)
        center = start - (step * month_index)
        return round(random.uniform(center - 1.5, center + 1.5), 1)

    return round(random.uniform(85.0, 95.0), 1)


def _behaviour_incidents(school: str) -> int:
    if school == "School B":
        return random.randint(8, 15)
    return random.randint(1, 5)


def _average_score(school: str) -> float:
    if school == "School A":
        return round(random.uniform(78.0, 88.0), 1)
    return round(random.uniform(65.0, 75.0), 1)


def _build_base_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    for school in SCHOOLS:
        for campus in CAMPUSES:
            for year_level in YEAR_LEVELS:
                for month_index, month in enumerate(MONTHS):
                    records.append(
                        {
                            "month": month,
                            "school": school,
                            "year_level": year_level,
                            "attendance_rate": _attendance_rate(school, month_index),
                            "behaviour_incidents": _behaviour_incidents(school),
                            "average_score": _average_score(school),
                            "campus": campus,
                            "program_type": random.choice(PROGRAM_TYPES),
                        }
                    )

    return records


def _inject_scenarios(records: list[dict[str, object]]) -> None:
    rng = random.Random(RANDOM_SEED)

    attendance_candidates = [
        index
        for index, record in enumerate(records)
        if record["school"] != "School C"
    ]
    attendance_indices = rng.sample(attendance_candidates, LOW_ATTENDANCE_COUNT)
    for index in attendance_indices:
        records[index]["attendance_rate"] = round(
            random.uniform(LOW_ATTENDANCE_MIN, LOW_ATTENDANCE_MAX),
            1,
        )

    remaining_indices = [
        index for index in range(len(records)) if index not in attendance_indices
    ]
    behaviour_indices = rng.sample(remaining_indices, HIGH_BEHAVIOUR_COUNT)
    for index in behaviour_indices:
        records[index]["behaviour_incidents"] = random.randint(
            HIGH_BEHAVIOUR_MIN,
            HIGH_BEHAVIOUR_MAX,
        )


def _summary(records: list[dict[str, object]]) -> None:
    behaviour_by_school: dict[str, int] = defaultdict(int)
    score_by_school: dict[str, list[float]] = defaultdict(list)
    attendance_by_school_month: dict[str, dict[str, float]] = defaultdict(dict)

    low_attendance_count = 0
    high_behaviour_count = 0

    for record in records:
        school = str(record["school"])
        month = str(record["month"])
        attendance = float(record["attendance_rate"])
        behaviour = int(record["behaviour_incidents"])
        average_score = float(record["average_score"])

        behaviour_by_school[school] += behaviour
        score_by_school[school].append(average_score)
        attendance_by_school_month[school][month] = (
            attendance_by_school_month[school].get(month, 0.0) + attendance
        )

        if LOW_ATTENDANCE_MIN <= attendance <= LOW_ATTENDANCE_MAX:
            low_attendance_count += 1
        if HIGH_BEHAVIOUR_MIN <= behaviour <= HIGH_BEHAVIOUR_MAX:
            high_behaviour_count += 1

    highest_behaviour_school = max(behaviour_by_school, key=behaviour_by_school.get)
    highest_score_school = max(
        score_by_school,
        key=lambda school: sum(score_by_school[school]) / len(score_by_school[school]),
    )
    school_c_attendance = [
        attendance_by_school_month["School C"][month]
        for month in MONTHS
        if month in attendance_by_school_month["School C"]
    ]

    print(f"total rows: {len(records)}")
    print(f"low attendance scenario count: {low_attendance_count}")
    print(f"high behaviour incident scenario count: {high_behaviour_count}")
    print(f"highest total behaviour incidents by school: {highest_behaviour_school}")
    print(f"highest average score by school: {highest_score_school}")
    print(
        "School C attendance trend (aggregate): "
        + ", ".join(f"{value:.1f}" for value in school_c_attendance)
    )
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
