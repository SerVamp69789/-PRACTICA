"""Совмещение JSON и Excel: новый студент добавляется, повтор даты — нет."""

from pathlib import Path

from openpyxl import Workbook

from attendance.storage import load_dataset


def _write_book(path: Path, students: list[tuple], marks: list[tuple]) -> None:
    book = Workbook()
    people = book.active
    people.title = "Студенты"
    people.append(["студент_id", "фио", "группа"])
    for row in students:
        people.append(list(row))
    marks_sheet = book.create_sheet("Посещаемость")
    marks_sheet.append(["студент_id", "дата", "присутствовал"])
    for row in marks:
        marks_sheet.append(list(row))
    book.save(path)


def test_excel_adds_student_and_does_not_double_same_day(tmp_path: Path):
    journal = tmp_path / "students.json"
    journal.write_text(
        """
        {
          "студенты": {"S1": {"фио": "Иванов Иван Иванович", "группа": "Г1"}},
          "посещаемость": [
            {"студент_id": "S1", "дата": "2026-11-02", "присутствовал": false}
          ]
        }
        """,
        encoding="utf-8",
    )
    excel = tmp_path / "journal.xlsx"
    _write_book(
        excel,
        [
            ("S1", "Иванов Иван Иванович", "Г1"),
            ("S2", "Соколова Анна Петровна", "2ИП-4-25"),
        ],
        [
            ("S1", "2026-11-02", False),
            ("S1", "2026-11-03", True),
            ("S2", "2026-11-02", False),
            ("S2", "2026-11-03", False),
        ],
    )
    dataset = load_dataset(journal, excel="auto")
    by_id = {student.student_id: student for student in dataset.students}
    assert by_id["S1"].lessons_total == 2
    assert by_id["S1"].absences == 1
    assert by_id["S2"].group == "2ИП-4-25"
    assert by_id["S2"].absences == 2
    assert "journal.xlsx" in dataset.source_name
