"""Расчёт пропусков и пороги мер.

Проверяем процент, границы 30/40/50 и то, что отчисление входит в отчёт на стипендию.
"""

import pytest

from attendance.analytics import (
    JournalError,
    absence_percent,
    build_students,
    classify,
    college_summary,
    group_summaries,
    students_at_least,
)
from attendance.models import (
    DEFAULT_RULES,
    STATUS_ATTENTION,
    STATUS_EXPULSION,
    STATUS_OK,
    STATUS_SCHOLARSHIP,
    Dataset,
    StudentRecord,
)


def test_absence_percent_basic():
    assert absence_percent(0, 10) == 0
    assert absence_percent(8, 10) == 80
    assert absence_percent(0, 0) == 0


def test_absence_percent_rejects_bad_counts():
    with pytest.raises(JournalError):
        absence_percent(-1, 10)
    with pytest.raises(JournalError):
        absence_percent(3, 2)


def test_classify_boundaries():
    rules = DEFAULT_RULES
    assert classify(29.9, rules) == STATUS_OK
    assert classify(30, rules) == STATUS_ATTENTION
    assert classify(39.9, rules) == STATUS_ATTENTION
    assert classify(40, rules) == STATUS_SCHOLARSHIP
    assert classify(49.9, rules) == STATUS_SCHOLARSHIP
    assert classify(50, rules) == STATUS_EXPULSION
    assert classify(80, rules) == STATUS_EXPULSION


def test_group_percent_is_weighted_by_lessons():
    students = (
        StudentRecord("a", "А", "Г1", 10, 1, ()),
        StudentRecord("b", "Б", "Г1", 30, 9, ()),
    )
    groups = group_summaries(students, DEFAULT_RULES)
    assert groups[0].code == "Г1"
    assert groups[0].absence_percent == pytest.approx(25)
    assert groups[0].attention == 1
    assert groups[0].scholarship == 0
    assert groups[0].headcount == 2


def test_groups_sorted_by_absence_desc():
    students = (
        StudentRecord("a", "А", "Спокойная", 10, 0, ()),
        StudentRecord("b", "Б", "Проблемная", 10, 8, ()),
    )
    codes = [group.code for group in group_summaries(students, DEFAULT_RULES)]
    assert codes == ["Проблемная", "Спокойная"]


def test_build_students_counts_absences_and_sorts_dates():
    data = {
        "студенты": {"S1": {"фио": "Иванов Иван", "группа": "Г1"}},
        "посещаемость": [
            {"студент_id": "S1", "дата": "2026-02-02", "присутствовал": False},
            {"студент_id": "S1", "дата": "2026-02-01", "присутствовал": True},
            {"студент_id": "S1", "дата": "2026-01-15", "присутствовал": False},
        ],
    }
    students, skipped = build_students(data)
    assert skipped == 0
    assert students[0].absences == 2
    assert students[0].lessons_total == 3
    assert students[0].absence_dates == ("2026-01-15", "2026-02-02")
    assert students[0].absence_percent == pytest.approx(200 / 3)


def test_unknown_attendance_id_is_skipped():
    data = {
        "студенты": {"S1": {"фио": "Иванов", "группа": "Г1"}},
        "посещаемость": [
            {"студент_id": "нет-такого", "дата": "2026-01-01", "присутствовал": False},
            {"студент_id": "S1", "дата": "2026-01-02", "присутствовал": True},
        ],
    }
    students, skipped = build_students(data)
    assert skipped == 1
    assert students[0].lessons_total == 1
    assert students[0].absences == 0


def test_broken_journal_and_flag():
    with pytest.raises(JournalError):
        build_students({"студенты": {}})
    with pytest.raises(JournalError):
        build_students(
            {
                "студенты": {"S1": {"фио": "Иванов", "группа": "Г1"}},
                "посещаемость": [{"студент_id": "S1", "присутствовал": "да"}],
            }
        )


def test_college_and_lists_use_same_thresholds():
    students = (
        StudentRecord("ok", "Норма", "Г1", 10, 1, ()),
        StudentRecord("att", "Внимание", "Г1", 10, 3, ()),
        StudentRecord("sch", "Стипендия", "Г2", 10, 4, ()),
        StudentRecord("exp", "Отчисление", "Г2", 10, 5, ()),
    )
    dataset = Dataset("тест.json", students, DEFAULT_RULES, 0)
    summary = college_summary(dataset)
    assert summary.headcount == 4
    assert summary.absences == 13
    assert summary.lessons_total == 40
    assert summary.absence_percent == pytest.approx(32.5)
    assert summary.attention == 1
    assert summary.scholarship == 1
    assert summary.expulsion == 1
    assert summary.lagging == 3

    lagging = [item.student_id for item in students_at_least(students, DEFAULT_RULES, STATUS_ATTENTION)]
    scholarship = [item.student_id for item in students_at_least(students, DEFAULT_RULES, STATUS_SCHOLARSHIP)]
    expulsion = [item.student_id for item in students_at_least(students, DEFAULT_RULES, STATUS_EXPULSION)]
    assert lagging == ["exp", "sch", "att"]
    assert scholarship == ["exp", "sch"]
    assert expulsion == ["exp"]


def test_group_code_is_spelled_out():
    from attendance.group_title import describe_group

    assert (
        describe_group("2ИП-2-25")
        == "2 курс группа 2 Информационные системы и программирование 2025 г"
    )
    assert (
        describe_group("2РКИ-1-25")
        == "2 курс группа 1 Разработка компьютерных игр и дополненной виртуальной реальности 2025 г"
    )
