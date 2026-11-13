"""Текстовые административные отчёты."""

from attendance.analytics import classify, college_summary, recommendation, students_at_least
from attendance.models import (
    STATUS_ATTENTION,
    STATUS_EXPULSION,
    STATUS_LABELS,
    STATUS_SCHOLARSHIP,
    CollegeSummary,
    Dataset,
    GroupSummary,
    StudentRecord,
)


def _percent(value: float) -> str:
    return f"{value:.1f}%"


def _rules_line(dataset: Dataset) -> str:
    rules = dataset.rules
    return (
        "Пороги: отстающий ≥ "
        f"{rules.attention_percent:.0f}%, лишение стипендии ≥ "
        f"{rules.scholarship_percent:.0f}%, отчисление ≥ "
        f"{rules.expulsion_percent:.0f}%."
    )


def _student_lines(students: tuple[StudentRecord, ...], rules) -> list[str]:
    if not students:
        return ["    Нет студентов по этому условию."]
    lines = ["    ФИО                            Группа      Занятий  Пропусков  Процент  Мера"]
    for student in students:
        status = STATUS_LABELS[classify(student.absence_percent, rules)]
        lines.append(
            f"    {student.full_name:<30} {student.group:<11} "
            f"{student.lessons_total:>7}  {student.absences:>9}  "
            f"{_percent(student.absence_percent):>7}  {status}"
        )
    return lines


def format_college(dataset: Dataset) -> str:
    """Purpose: сводный отчёт по всему колледжу.
    Inputs: dataset — журнал.
    Output: многострочный текст со сводкой и таблицей групп.
    Why: администрации нужен один документ по дисциплине всего заведения.
    """
    summary = college_summary(dataset)
    lines = [
        "СВОДНЫЙ ОТЧЁТ ПО КОЛЛЕДЖУ",
        f"Источник: {dataset.source_name}",
        _rules_line(dataset),
        "",
        f"Студентов: {summary.headcount}",
        f"Групп: {len(summary.groups)}",
        f"Занятий: {summary.lessons_total}",
        f"Пропусков: {summary.absences}",
        f"Процент пропусков: {_percent(summary.absence_percent)}",
        f"Отстающие (от {dataset.rules.attention_percent:.0f}%): {summary.lagging}",
        f"    из них только внимание: {summary.attention}",
        f"    лишение стипендии: {summary.scholarship}",
        f"    отчисление: {summary.expulsion}",
        "",
        "Группа       Студентов  Занятий  Пропусков  Процент  Внимание  Стипендия  Отчисление",
    ]
    for group in summary.groups:
        lines.append(
            f"{group.code:<12} {group.headcount:>9}  {group.lessons_total:>7}  "
            f"{group.absences:>9}  {_percent(group.absence_percent):>7}  "
            f"{group.attention:>8}  {group.scholarship:>9}  {group.expulsion:>10}"
        )
    if summary.skipped_records:
        lines.extend(["", f"Пропущено отметок с неизвестным студентом: {summary.skipped_records}."])
    lines.extend(["", _college_advice(summary)])
    return "\n".join(lines)


def format_group(group: GroupSummary, dataset: Dataset) -> str:
    """Purpose: список студентов выбранной группы.
    Inputs: group — сводка группы, dataset — журнал с порогами.
    Output: текст со сводкой группы и таблицей студентов.
    Why: после выбора группы администратор смотрит людей, а не только общий процент.
    """
    lines = [
        f"ГРУППА {group.code}",
        _rules_line(dataset),
        "",
        f"Студентов: {group.headcount}",
        f"Занятий: {group.lessons_total}",
        f"Пропусков: {group.absences}",
        f"Процент пропусков: {_percent(group.absence_percent)}",
        f"Внимание: {group.attention}  |  стипендия: {group.scholarship}  |  отчисление: {group.expulsion}",
        "",
        *_student_lines(group.students, dataset.rules),
    ]
    return "\n".join(lines)


def format_student(student: StudentRecord, dataset: Dataset) -> str:
    """Purpose: карточка одного студента с датами пропусков.
    Inputs: student — итог человека, dataset — пороги.
    Output: текст карточки и рекомендуемая мера.
    Why: для приказа нужны не только процент, но и даты, на которые он опирается.
    """
    status = classify(student.absence_percent, dataset.rules)
    dates = ", ".join(student.absence_dates) if student.absence_dates else "нет"
    return "\n".join(
        [
            student.full_name,
            f"Группа: {student.group}",
            f"Занятий: {student.lessons_total}",
            f"Присутствовал: {student.presents}",
            f"Пропусков: {student.absences} ({_percent(student.absence_percent)})",
            f"Даты пропусков: {dates}",
            f"Статус: {STATUS_LABELS[status]}",
            recommendation(status),
        ]
    )


def format_lagging(dataset: Dataset) -> str:
    """Purpose: список студентов, которых уже нужно заметить.
    Inputs: dataset — журнал.
    Output: текст отчёта по порогу внимания и выше.
    Why: цель системы — вовремя выявлять отстающих по всему колледжу.
    """
    selected = students_at_least(dataset.students, dataset.rules, STATUS_ATTENTION)
    lines = [
        "ОТСТАЮЩИЕ СТУДЕНТЫ",
        f"Пропуски от {dataset.rules.attention_percent:.0f}% и выше, включая кандидатов на стипендию и отчисление.",
        f"Человек в списке: {len(selected)}",
        "",
        *_student_lines(selected, dataset.rules),
    ]
    return "\n".join(lines)


def format_scholarship(dataset: Dataset) -> str:
    """Purpose: отчёт для лишения стипендии.
    Inputs: dataset — журнал.
    Output: студенты с процентом пропусков не ниже порога стипендии.
    Why: деканату нужен отдельный список, а не общий журнал.
    """
    selected = students_at_least(dataset.students, dataset.rules, STATUS_SCHOLARSHIP)
    lines = [
        "ОТЧЁТ ДЛЯ ЛИШЕНИЯ СТИПЕНДИИ",
        f"Пропуски от {dataset.rules.scholarship_percent:.0f}%.",
        "Студенты с порогом отчисления тоже включены: стипендия при отчислении не сохраняется.",
        f"Человек в списке: {len(selected)}",
        "",
        *_student_lines(selected, dataset.rules),
    ]
    return "\n".join(lines)


def format_expulsion(dataset: Dataset) -> str:
    """Purpose: отчёт для отчисления.
    Inputs: dataset — журнал.
    Output: студенты с процентом пропусков не ниже порога отчисления.
    Why: это отдельное административное решение, строже лишения стипендии.
    """
    selected = students_at_least(dataset.students, dataset.rules, STATUS_EXPULSION)
    lines = [
        "ОТЧЁТ ДЛЯ ОТЧИСЛЕНИЯ",
        f"Пропуски от {dataset.rules.expulsion_percent:.0f}%.",
        f"Человек в списке: {len(selected)}",
        "",
        *_student_lines(selected, dataset.rules),
    ]
    return "\n".join(lines)


def _college_advice(summary: CollegeSummary) -> str:
    if summary.expulsion:
        return (
            f"Рекомендация: в первую очередь разобрать {summary.expulsion} "
            "студент(ов) с порогом отчисления, затем список на лишение стипендии."
        )
    if summary.scholarship:
        return "Рекомендация: подготовить материалы на лишение стипендии. Кандидатов на отчисление нет."
    if summary.lagging:
        return "Рекомендация: провести беседы с отстающими. До лишения стипендии и отчисления никто не дошёл."
    return "Рекомендация: по текущим порогам дисциплина колледжа в норме."


def report_bundle(dataset: Dataset) -> dict[str, str]:
    """Purpose: собрать все административные тексты для записи на диск.
    Inputs: dataset — журнал.
    Output: имя файла без пути → текст отчёта.
    Why: пункт меню «сохранить» и флаг --save пишут один и тот же комплект.
    """
    summary = college_summary(dataset)
    files = {
        "сводный-отчёт.txt": format_college(dataset),
        "отстающие.txt": format_lagging(dataset),
        "лишение-стипендии.txt": format_scholarship(dataset),
        "отчисление.txt": format_expulsion(dataset),
    }
    for group in summary.groups:
        safe_code = group.code.replace("/", "-").replace("\\", "-")
        files[f"группа-{safe_code}.txt"] = format_group(group, dataset)
    return files
