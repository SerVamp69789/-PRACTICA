"""Расчёт процента пропусков и разложение студентов по мерам."""

from attendance.models import (
    STATUS_ATTENTION,
    STATUS_EXPULSION,
    STATUS_OK,
    STATUS_RANK,
    STATUS_SCHOLARSHIP,
    CollegeSummary,
    Dataset,
    GroupSummary,
    Rules,
    StudentRecord,
)


class JournalError(ValueError):
    """Журнал не сходится: нет обязательных полей или отметки противоречат друг другу."""


def absence_percent(absences: int, lessons: int) -> float:
    """Purpose: доля пропущенных занятий.
    Inputs: absences — число пропусков, lessons — число занятий студента.
    Output: процент от 0 до 100; при нуле занятий возвращает 0.
    Why: отчёты сравнивают группы и студентов одной шкалой, а не сырым числом пропусков.
    """
    if lessons < 0 or absences < 0:
        raise JournalError("Число занятий и пропусков не может быть отрицательным.")
    if absences > lessons:
        raise JournalError("Пропусков больше, чем занятий.")
    if lessons == 0:
        return 0.0
    return absences / lessons * 100.0


def classify(percent: float, rules: Rules) -> str:
    """Purpose: выбрать административную меру по проценту пропусков.
    Inputs: percent — процент пропусков, rules — пороги внимания, стипендии и отчисления.
    Output: код статуса ok / attention / scholarship / expulsion.
    Why: списки на стипендию и отчисление должны собираться одним правилом, без ручной сортировки.
    """
    # Сначала самая строгая мера, иначе отчисленный попадёт только в стипендию.
    if percent >= rules.expulsion_percent:
        return STATUS_EXPULSION
    if percent >= rules.scholarship_percent:
        return STATUS_SCHOLARSHIP
    if percent >= rules.attention_percent:
        return STATUS_ATTENTION
    return STATUS_OK


def recommendation(status: str) -> str:
    """Purpose: текст меры для карточки студента и отчёта.
    Inputs: status — код из classify.
    Output: короткая формулировка для администрации.
    Why: отчёт должен говорить, что делать с человеком, а не только показывать процент.
    """
    texts = {
        STATUS_OK: "Дисциплина в норме, мер не требуется.",
        STATUS_ATTENTION: "Усилить контроль: беседа куратора и предупреждение.",
        STATUS_SCHOLARSHIP: "Подготовить материалы на лишение стипендии. Это не отчисление: студент остаётся в группе.",
        STATUS_EXPULSION: "Подготовить материалы на отчисление. Стипендия при отчислении снимается тоже.",
    }
    try:
        return texts[status]
    except KeyError as error:
        raise JournalError(f"Неизвестный статус: {status}") from error


def build_students(data: dict) -> tuple[tuple[StudentRecord, ...], int]:
    """Purpose: свернуть журнал отметок в итог по каждому студенту.
    Inputs: data — словарь с ключами «студенты» и «посещаемость», как в students.json.
    Output: кортеж студентов и число отметок, которые ссылаются на неизвестный id.
    Why: административные проценты считаются по людям и группам, а не по сырым строкам журнала.
    """
    if not isinstance(data, dict):
        raise JournalError("Журнал должен быть объектом JSON.")
    raw_students = data.get("студенты")
    raw_attendance = data.get("посещаемость")
    if not isinstance(raw_students, dict) or not isinstance(raw_attendance, list):
        raise JournalError("В журнале нужны объекты «студенты» и список «посещаемость».")

    # Отдельные счётчики: сколько занятий было и сколько из них пропущено.
    lessons: dict[str, int] = {student_id: 0 for student_id in raw_students}
    absences: dict[str, int] = {student_id: 0 for student_id in raw_students}
    dates: dict[str, list[str]] = {student_id: [] for student_id in raw_students}
    skipped = 0

    for record in raw_attendance:
        if not isinstance(record, dict):
            raise JournalError("Запись посещаемости должна быть объектом.")
        student_id = record.get("студент_id")
        # Чужой id не ломает журнал, но такие отметки не входят в процент.
        if student_id not in raw_students:
            skipped += 1
            continue
        present = record.get("присутствовал")
        if not isinstance(present, bool):
            raise JournalError(f"У {student_id} поле «присутствовал» должно быть true или false.")
        lessons[student_id] += 1
        if not present:
            absences[student_id] += 1
            date = record.get("дата")
            if isinstance(date, str) and date:
                dates[student_id].append(date)

    records = []
    for student_id, info in raw_students.items():
        if not isinstance(info, dict):
            raise JournalError(f"Карточка {student_id} должна быть объектом.")
        name = info.get("фио") or "—"
        group = info.get("группа") or "—"
        records.append(
            StudentRecord(
                student_id=str(student_id),
                full_name=str(name),
                group=str(group),
                lessons_total=lessons[student_id],
                absences=absences[student_id],
                absence_dates=tuple(sorted(dates[student_id])),
            )
        )
    records.sort(key=lambda item: (-item.absence_percent, item.group, item.full_name))
    return tuple(records), skipped


def group_summaries(students: tuple[StudentRecord, ...], rules: Rules) -> tuple[GroupSummary, ...]:
    """Purpose: агрегировать студентов по учебным группам.
    Inputs: students — итоги людей, rules — пороги мер.
    Output: группы по убыванию процента пропусков.
    Why: деканат смотрит дисциплину группы целиком, а не только отдельных фамилий.
    """
    by_code: dict[str, list[StudentRecord]] = {}
    for student in students:
        by_code.setdefault(student.group, []).append(student)

    summaries = []
    for code, members in by_code.items():
        ordered = tuple(sorted(members, key=lambda item: (-item.absence_percent, item.full_name)))
        # Процент группы считается по всем занятиям, а не как среднее процентов студентов.
        lessons = sum(item.lessons_total for item in ordered)
        missed = sum(item.absences for item in ordered)
        statuses = [classify(item.absence_percent, rules) for item in ordered]
        summaries.append(
            GroupSummary(
                code=code,
                students=ordered,
                lessons_total=lessons,
                absences=missed,
                absence_percent=absence_percent(missed, lessons),
                attention=statuses.count(STATUS_ATTENTION),
                scholarship=statuses.count(STATUS_SCHOLARSHIP),
                expulsion=statuses.count(STATUS_EXPULSION),
            )
        )
    summaries.sort(key=lambda item: (-item.absence_percent, item.code))
    return tuple(summaries)


def college_summary(dataset: Dataset) -> CollegeSummary:
    """Purpose: собрать сводку по всем группам журнала.
    Inputs: dataset — загруженный журнал.
    Output: итог колледжа и группы внутри него.
    Why: задание требует агрегировать данные всего учебного заведения, а не одной группы.
    """
    groups = group_summaries(dataset.students, dataset.rules)
    lessons = sum(group.lessons_total for group in groups)
    missed = sum(group.absences for group in groups)
    return CollegeSummary(
        groups=groups,
        lessons_total=lessons,
        absences=missed,
        absence_percent=absence_percent(missed, lessons),
        skipped_records=dataset.skipped_records,
    )


def students_at_least(students: tuple[StudentRecord, ...], rules: Rules, min_status: str) -> tuple[StudentRecord, ...]:
    """Purpose: отобрать студентов не мягче заданной меры.
    Inputs: students — люди, rules — пороги, min_status — нижняя мера (attention, scholarship или expulsion).
    Output: студенты этой меры и строже, по убыванию процента пропусков.
    Why: отчисление включает лишение стипендии, поэтому такие студенты входят в отчёт на стипендию. Обратное неверно: одна только стипендия до отчисления не доходит.
    """
    # В выборку входят эта мера и все более строгие.
    minimum = STATUS_RANK[min_status]
    selected = [
        student
        for student in students
        if STATUS_RANK[classify(student.absence_percent, rules)] >= minimum
    ]
    selected.sort(key=lambda item: (-item.absence_percent, item.group, item.full_name))
    return tuple(selected)
