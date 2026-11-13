"""Чтение журнала из JSON и Excel."""

import json
from pathlib import Path

from attendance.analytics import JournalError, build_students
from attendance.excel_journal import merge_journals, read_excel_journal
from attendance.models import DEFAULT_RULES, Dataset


def _read_json(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise JournalError(f"Не удалось открыть журнал: {path}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise JournalError(f"Журнал не является JSON: {path}") from error
    return data


def load_dataset(path: Path, rules=DEFAULT_RULES, excel: Path | None | str = "auto") -> Dataset:
    """Purpose: прочитать JSON и, если есть, совместить его с книгой Excel.
    Inputs: path — students.json, rules — пороги, excel — путь к xlsx, «auto» или None.
    Output: Dataset по объединённому журналу.
    Why: часть данных лежит в JSON, часть в таблице, а проценты считаются по всем группам сразу.
    """
    data = _read_json(path)
    source_name = path.name
    excel_path = None
    if excel == "auto":
        candidate = path.with_name("journal.xlsx")
        if candidate.is_file():
            excel_path = candidate
    elif excel:
        excel_path = Path(excel)
        if not excel_path.is_file():
            raise JournalError(f"Не удалось открыть Excel: {excel_path}")
    if excel_path is not None:
        data = merge_journals(data, read_excel_journal(excel_path))
        source_name = f"{path.name} + {excel_path.name}"
    students, skipped = build_students(data)
    return Dataset(
        source_name=source_name,
        students=students,
        rules=rules,
        skipped_records=skipped,
    )
