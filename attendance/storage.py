"""Чтение журнала students.json."""

import json
from pathlib import Path

from attendance.analytics import JournalError, build_students
from attendance.models import DEFAULT_RULES, Dataset


def load_dataset(path: Path, rules=DEFAULT_RULES) -> Dataset:
    """Purpose: прочитать журнал с диска и свернуть его в студентов.
    Inputs: path — файл JSON, rules — пороги мер.
    Output: Dataset с итогами и числом пропущенных чужих отметок.
    Why: меню и отчёты работают с одним уже проверенным набором, а не читают файл на каждый экран.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise JournalError(f"Не удалось открыть журнал: {path}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise JournalError(f"Журнал не является JSON: {path}") from error
    students, skipped = build_students(data)
    return Dataset(
        source_name=path.name,
        students=students,
        rules=rules,
        skipped_records=skipped,
    )
