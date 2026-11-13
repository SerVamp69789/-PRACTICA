"""Модель журнала: студент, группа, правила мер."""

from dataclasses import dataclass


ATTENTION_PERCENT = 30.0
SCHOLARSHIP_PERCENT = 40.0
EXPULSION_PERCENT = 50.0

STATUS_OK = "ok"
STATUS_ATTENTION = "attention"
STATUS_SCHOLARSHIP = "scholarship"
STATUS_EXPULSION = "expulsion"

STATUS_LABELS = {
    STATUS_OK: "норма",
    STATUS_ATTENTION: "отстающий",
    STATUS_SCHOLARSHIP: "лишение стипендии",
    STATUS_EXPULSION: "отчисление",
}

STATUS_RANK = {
    STATUS_OK: 0,
    STATUS_ATTENTION: 1,
    STATUS_SCHOLARSHIP: 2,
    STATUS_EXPULSION: 3,
}


@dataclass(frozen=True)
class Rules:
    """Пороги процента пропусков для мер администрации."""

    attention_percent: float = ATTENTION_PERCENT
    scholarship_percent: float = SCHOLARSHIP_PERCENT
    expulsion_percent: float = EXPULSION_PERCENT


DEFAULT_RULES = Rules()


@dataclass(frozen=True)
class StudentRecord:
    """Итог одного студента за период журнала."""

    student_id: str
    full_name: str
    group: str
    lessons_total: int
    absences: int
    absence_dates: tuple[str, ...]

    @property
    def presents(self) -> int:
        return self.lessons_total - self.absences

    @property
    def absence_percent(self) -> float:
        if self.lessons_total <= 0:
            return 0.0
        return self.absences / self.lessons_total * 100.0


@dataclass(frozen=True)
class GroupSummary:
    """Сводка по одной учебной группе."""

    code: str
    students: tuple[StudentRecord, ...]
    lessons_total: int
    absences: int
    absence_percent: float
    attention: int
    scholarship: int
    expulsion: int

    @property
    def headcount(self) -> int:
        return len(self.students)

    @property
    def lagging(self) -> int:
        return self.attention + self.scholarship + self.expulsion


@dataclass(frozen=True)
class CollegeSummary:
    """Сводка по всему колледжу."""

    groups: tuple[GroupSummary, ...]
    lessons_total: int
    absences: int
    absence_percent: float
    skipped_records: int

    @property
    def headcount(self) -> int:
        return sum(group.headcount for group in self.groups)

    @property
    def attention(self) -> int:
        return sum(group.attention for group in self.groups)

    @property
    def scholarship(self) -> int:
        return sum(group.scholarship for group in self.groups)

    @property
    def expulsion(self) -> int:
        return sum(group.expulsion for group in self.groups)

    @property
    def lagging(self) -> int:
        return self.attention + self.scholarship + self.expulsion


@dataclass(frozen=True)
class Dataset:
    """Загруженный журнал и правила, по которым его читают."""

    source_name: str
    students: tuple[StudentRecord, ...]
    rules: Rules
    skipped_records: int
