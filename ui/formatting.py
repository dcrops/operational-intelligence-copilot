"""Reusable UI formatting helpers."""

_PRESERVED_ABBREVIATIONS = {
    "id",
    "uuid",
    "kpi",
    "hr",
    "url",
}


def format_column_label(column_name: str) -> str:
    """
    Convert a schema column name into a human-friendly label.

    Examples:
        defects -> Defects
        downtime_minutes -> Downtime Minutes
        employee_id -> Employee ID
    """
    spaced = column_name.strip().replace("_", " ")
    words = spaced.split()
    formatted_words: list[str] = []

    for word in words:
        lower_word = word.lower()
        if lower_word in _PRESERVED_ABBREVIATIONS:
            formatted_words.append(lower_word.upper())
        else:
            formatted_words.append(lower_word.capitalize())

    return " ".join(formatted_words)
