"""Чтение журнала из книги Excel."""

from pathlib import Path

from openpyxl import load_workbook

from attendance.analytics import JournalError

STUDENTS_SHEET = "Студенты"
ATTENDANCE_SHEET = "Посещаемость"


def _as_bool(value, student_id: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(int(value))
    if isinstance(value, str):
        text = value.strip().casefold()
        if text in {"true", "да", "1", "присутствовал"}:
            return True
        if text in {"false", "нет", "0", "отсутствовал"}:
            return False
    raise JournalError(f"У {student_id} в Excel поле «присутствовал» должно быть да или нет.")


def _header_map(row) -> dict[str, int]:
    mapping = {}
    for index, cell in enumerate(row):
        if cell is None:
            continue
        mapping[str(cell).strip().casefold()] = index
    return mapping


def _cell(row: tuple, mapping: dict[str, int], name: str):
    index = mapping.get(name.casefold())
    if index is None or index >= len(row):
        return None
    return row[index]


def read_excel_journal(path: Path) -> dict:
    """Purpose: прочитать студентов и отметки из книги Excel.
    Inputs: path — файл xlsx с листами «Студенты» и «Посещаемость».
    Output: словарь той же формы, что students.json.
    Why: деканат ведёт часть журнала в таблице, а программа считает по общим данным.
    """
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except OSError as error:
        raise JournalError(f"Не удалось открыть Excel: {path}") from error
    try:
        if STUDENTS_SHEET not in workbook.sheetnames or ATTENDANCE_SHEET not in workbook.sheetnames:
            raise JournalError("В Excel нужны листы «Студенты» и «Посещаемость».")
        students: dict[str, dict] = {}
        student_rows = workbook[STUDENTS_SHEET].iter_rows(values_only=True)
        student_header = _header_map(next(student_rows, ()))
        for row in student_rows:
            student_id = _cell(row, student_header, "студент_id")
            if student_id is None or str(student_id).strip() == "":
                continue
            student_id = str(student_id).strip()
            name = _cell(row, student_header, "фио") or "—"
            group = _cell(row, student_header, "группа") or "—"
            students[student_id] = {"фио": str(name).strip(), "группа": str(group).strip()}

        attendance = []
        mark_rows = workbook[ATTENDANCE_SHEET].iter_rows(values_only=True)
        mark_header = _header_map(next(mark_rows, ()))
        for row in mark_rows:
            student_id = _cell(row, mark_header, "студент_id")
            if student_id is None or str(student_id).strip() == "":
                continue
            student_id = str(student_id).strip()
            date = _cell(row, mark_header, "дата")
            present = _as_bool(_cell(row, mark_header, "присутствовал"), student_id)
            attendance.append(
                {
                    "студент_id": student_id,
                    "дата": str(date).strip() if date is not None else "",
                    "присутствовал": present,
                }
            )
    finally:
        workbook.close()
    return {"студенты": students, "посещаемость": attendance}


def merge_journals(base: dict, extra: dict) -> dict:
    """Purpose: сложить журнал JSON и журнал Excel без двойного учёта.
    Inputs: base — первый источник, extra — второй.
    Output: один журнал. Повтор того же студента и той же даты берётся из base.
    Why: одни и те же люди лежат в обоих файлах, а отчёт должен посчитать занятие один раз.
    """
    students = dict(base.get("студенты") or {})
    for student_id, info in (extra.get("студенты") or {}).items():
        students.setdefault(student_id, info)
    seen = set()
    attendance = []
    for record in list(base.get("посещаемость") or []) + list(extra.get("посещаемость") or []):
        if not isinstance(record, dict):
            continue
        key = (record.get("студент_id"), record.get("дата"))
        if key in seen:
            continue
        seen.add(key)
        attendance.append(record)
    return {"студенты": students, "посещаемость": attendance}
