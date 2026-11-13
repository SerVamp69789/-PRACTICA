"""Отчёты и чтение настоящего students.json."""

from pathlib import Path

import pytest

from attendance.analytics import classify
from attendance.models import STATUS_EXPULSION, STATUS_OK, STATUS_SCHOLARSHIP
from attendance.reports import format_college, format_expulsion, format_scholarship, format_student
from attendance.storage import load_dataset

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "students.json"


@pytest.fixture(scope="module")
def dataset():
    return load_dataset(JOURNAL)


NEW_GROUPS = {
    "2ИП-4-25": 26,
    "2ИП-5-25": 27,
    "2ИП-6-25": 28,
    "2ИП-7-25": 29,
    "2ИП-8-25": 30,
    "2РКИ-1-25": 28,
    "2РКИ-2-25": 30,
}


def test_real_journal_shape(dataset):
    assert dataset.source_name == "students.json + journal.xlsx"
    assert dataset.skipped_records == 0
    codes = {student.group for student in dataset.students}
    assert {"2ИП-1-25", "2ИП-2-25", "2ИП-3-25"} <= codes
    assert set(NEW_GROUPS) <= codes
    for code, size in NEW_GROUPS.items():
        assert sum(student.group == code for student in dataset.students) == size
    assert all(student.lessons_total == 10 for student in dataset.students)
    assert len(dataset.students) == 84 + sum(NEW_GROUPS.values())


def test_known_students_land_in_expected_lists(dataset):
    by_name = {student.full_name: student for student in dataset.students}
    zero = by_name["Попов Жора Николаевич"]
    scholarship = by_name["Морозова Мария Ивановна"]
    expulsion = by_name["Фомин Юрий Ильич"]

    assert classify(zero.absence_percent, dataset.rules) == STATUS_OK
    assert scholarship.absences == 4
    assert classify(scholarship.absence_percent, dataset.rules) == STATUS_SCHOLARSHIP
    assert expulsion.absences == 8
    assert classify(expulsion.absence_percent, dataset.rules) == STATUS_EXPULSION

    scholarship_text = format_scholarship(dataset)
    expulsion_text = format_expulsion(dataset)
    assert "Лишение стипендии не означает отчисление" in scholarship_text
    assert "Фомин Юрий Ильич" in scholarship_text
    assert "Фомин Юрий Ильич" in expulsion_text
    assert "Морозова Мария Ивановна" in scholarship_text
    assert "Морозова Мария Ивановна" not in expulsion_text
    assert "Попов Жора Николаевич" not in scholarship_text
    assert "Попов Жора Николаевич" not in expulsion_text
    assert expulsion.absences == 8


def test_college_report_matches_raw_marks(dataset):
    text = format_college(dataset)
    missed = sum(student.absences for student in dataset.students)
    assert f"Студентов: {len(dataset.students)}" in text
    assert "2ИП-8-25" in text and "2РКИ-2-25" in text
    assert f"Пропусков: {missed}" in text
    assert "2ИП-1-25" in text and "2ИП-2-25" in text and "2ИП-3-25" in text


def test_student_card_lists_absence_dates(dataset):
    student = next(item for item in dataset.students if item.full_name == "Фомин Юрий Ильич")
    card = format_student(student, dataset)
    assert "2ИП-2-25" in card
    assert "Пропусков: 8 (80.0%)" in card
    assert "отчисление" in card
    assert student.absence_dates[0] in card
    assert len(student.absence_dates) == 8
