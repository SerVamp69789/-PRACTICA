"""Меню: группы, студенты выбранной группы, отчёты."""

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from attendance.analytics import classify, college_summary
from attendance.models import (
    STATUS_ATTENTION,
    STATUS_EXPULSION,
    STATUS_LABELS,
    STATUS_OK,
    STATUS_SCHOLARSHIP,
    Dataset,
    GroupSummary,
)
from attendance.reports import (
    format_college,
    format_expulsion,
    format_group,
    format_lagging,
    format_scholarship,
    format_student,
    report_bundle,
)

STATUS_STYLE = {
    STATUS_OK: "green",
    STATUS_ATTENTION: "yellow",
    STATUS_SCHOLARSHIP: "magenta",
    STATUS_EXPULSION: "bold red",
}


def _bar(percent: float, width: int = 10) -> Text:
    filled = round(percent / 100 * width)
    filled = max(0, min(width, filled))
    return Text("█" * filled + "░" * (width - filled))


def _status_text(status: str) -> Text:
    return Text(STATUS_LABELS[status], style=STATUS_STYLE[status])


def _paint(percent: float, dataset: Dataset, label: str) -> Text:
    status = classify(percent, dataset.rules)
    return Text(label, style=STATUS_STYLE[status])


def _ordered_groups(dataset: Dataset) -> list[GroupSummary]:
    groups = list(college_summary(dataset).groups)
    groups.sort(key=lambda group: group.code)
    return groups


def _clear(console: Console) -> None:
    try:
        console.clear()
    except (OSError, AttributeError):
        console.print()


def _pause(console: Console) -> None:
    Prompt.ask("\n[dim]Enter — назад[/dim]", default="", show_default=False)


def render_home(console: Console, dataset: Dataset) -> None:
    """Purpose: главный экран — список групп и команды административных отчётов.
    Inputs: console — вывод rich, dataset — журнал.
    Output: ничего, рисует панель и таблицу групп.
    Why: задание просит меню со списком групп; номер группы открывает её студентов.
    """
    summary = college_summary(dataset)
    headline = Text()
    headline.append("СИСТЕМА КОНТРОЛЯ ПОСЕЩАЕМОСТИ\n", style="bold bright_white")
    headline.append("Аналитика и администрирование учебного заведения\n", style="cyan")
    headline.append(
        "Лишение стипендии не отчисляет. Отчисление снимает и стипендию.\n",
        style="yellow",
    )
    headline.append(f"Журнал {dataset.source_name}\n", style="dim")
    headline.append(
        f"Групп {len(summary.groups)}    студентов {summary.headcount}    "
        f"пропуски {summary.absence_percent:.1f}%\n",
        style="white",
    )
    bar = _bar(summary.absence_percent)
    bar.style = "bright_cyan"
    headline.append(bar)
    headline.append(
        f"\nОтстающие {summary.lagging}    только стипендия {summary.scholarship}    "
        f"отчисление {summary.expulsion}",
        style="white",
    )
    console.print(Panel(headline, box=box.DOUBLE, border_style="bright_cyan", padding=(1, 2)))
    console.print(_groups_table(dataset))
    menu = Table.grid(padding=(0, 2))
    menu.add_column(style="bold cyan", justify="right")
    menu.add_column()
    items = [
        ("номер", "список студентов выбранной группы"),
        ("сводка", "сводный административный отчёт по всем группам"),
        ("отстающие", "выявить отстающих студентов"),
        ("стипендия", "отчёт для лишения стипендии"),
        ("отчисление", "отчёт для отчисления"),
        ("сохранить", "записать отчёты в reports/"),
        ("0", "выход"),
    ]
    for key, label in items:
        menu.add_row(key, label)
    console.print(Panel(menu, title="Команды", border_style="bright_black"))


def _groups_table(dataset: Dataset) -> Table:
    table = Table(
        title="Группы колледжа",
        caption="Номер открывает студентов. Стип. — только стипендия, без отчисления.",
        box=box.ROUNDED,
        header_style="bold bright_white on dark_cyan",
        border_style="bright_cyan",
        caption_style="dim",
        expand=False,
        padding=(0, 1),
    )
    table.add_column("№", justify="right", width=3, no_wrap=True, style="bold bright_cyan")
    table.add_column("Группа", width=11, no_wrap=True, style="bold")
    table.add_column("Чел.", justify="right", width=4, no_wrap=True)
    table.add_column("%", justify="right", width=5, no_wrap=True)
    table.add_column("Шкала", width=10, no_wrap=True)
    table.add_column("Вним.", justify="right", width=5, no_wrap=True)
    table.add_column("Стип.", justify="right", width=5, no_wrap=True)
    table.add_column("Отч.", justify="right", width=4, no_wrap=True)
    for index, group in enumerate(_ordered_groups(dataset), start=1):
        bar = _bar(group.absence_percent)
        bar.style = STATUS_STYLE[classify(group.absence_percent, dataset.rules)]
        table.add_row(
            str(index),
            group.code,
            str(group.headcount),
            _paint(group.absence_percent, dataset, f"{group.absence_percent:.1f}"),
            bar,
            str(group.attention),
            str(group.scholarship),
            Text(str(group.expulsion), style="bold red" if group.expulsion else "green"),
        )
    return table


def _students_table(group: GroupSummary, dataset: Dataset) -> Table:
    table = Table(
        title=f"{group.code}  ·  пропуски {group.absence_percent:.1f}%  ·  {group.headcount} студентов",
        box=box.ROUNDED,
        header_style="bold bright_white on dark_cyan",
        border_style="bright_cyan",
        expand=False,
        padding=(0, 1),
    )
    table.add_column("№", justify="right", width=3, no_wrap=True, style="bold bright_cyan")
    table.add_column("Студент", min_width=28, no_wrap=True)
    table.add_column("Проп.", justify="right", width=5, no_wrap=True)
    table.add_column("%", justify="right", width=5, no_wrap=True)
    table.add_column("Шкала", width=10, no_wrap=True)
    table.add_column("Статус", min_width=18, no_wrap=True)
    for index, student in enumerate(group.students, start=1):
        status = classify(student.absence_percent, dataset.rules)
        bar = _bar(student.absence_percent)
        bar.style = STATUS_STYLE[status]
        table.add_row(
            str(index),
            student.full_name,
            f"{student.absences}/{student.lessons_total}",
            _paint(student.absence_percent, dataset, f"{student.absence_percent:.1f}"),
            bar,
            _status_text(status),
        )
    return table


def _resolve_group(dataset: Dataset, raw: str) -> GroupSummary | None:
    groups = _ordered_groups(dataset)
    if raw.isdigit():
        number = int(raw)
        if 1 <= number <= len(groups):
            return groups[number - 1]
    for group in groups:
        if group.code == raw:
            return group
    return None


def _show_text(console: Console, title: str, text: str) -> None:
    console.clear()
    console.print(Panel(text, title=title, border_style="cyan", box=box.ROUNDED))
    _pause(console)


def browse_group(console: Console, dataset: Dataset, group: GroupSummary) -> None:
    """Purpose: показать студентов группы и открыть карточку по номеру.
    Inputs: console, dataset, group — выбранная группа.
    Output: ничего, держит экран, пока не выбран возврат.
    Why: задание просит после выбора группы показать список студентов.
    """
    while True:
        _clear(console)
        console.print(_students_table(group, dataset))
        console.print(
            f"[dim]Внимание {group.attention} · стипендия {group.scholarship} · "
            f"отчисление {group.expulsion}. Номер студента — карточка, 0 — к группам.[/dim]"
        )
        raw = Prompt.ask("Студент").strip()
        if raw == "0":
            return
        if not raw.isdigit() or not 1 <= int(raw) <= len(group.students):
            console.print("[red]Нет студента с таким номером.[/red]")
            _pause(console)
            continue
        student = group.students[int(raw) - 1]
        _show_text(console, student.full_name, format_student(student, dataset))


def save_reports(dataset: Dataset, directory: Path) -> list[Path]:
    """Purpose: записать комплект отчётов в папку.
    Inputs: dataset — журнал, directory — каталог назначения.
    Output: пути созданных файлов.
    Why: отчёты на отчисление и стипендию нужно отдавать файлом, а не только смотреть на экране.
    """
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in report_bundle(dataset).items():
        path = directory / name
        path.write_text(text + "\n", encoding="utf-8")
        written.append(path)
    return written


def run_menu(dataset: Dataset) -> None:
    """Purpose: цикл меню: группа открывает студентов, команды открывают отчёты.
    Inputs: dataset — загруженный журнал.
    Output: ничего, завершается по команде «0» или Ctrl+C.
    Why: администратор с первого экрана видит группы и сразу выбирает одну из них.
    """
    console = Console(highlight=False)
    commands = {
        "сводка": lambda: _show_text(console, "Сводный административный отчёт", format_college(dataset)),
        "отстающие": lambda: _show_text(console, "Отстающие студенты", format_lagging(dataset)),
        "стипендия": lambda: _show_text(console, "Отчёт для лишения стипендии", format_scholarship(dataset)),
        "отчисление": lambda: _show_text(console, "Отчёт для отчисления", format_expulsion(dataset)),
    }
    try:
        while True:
            _clear(console)
            render_home(console, dataset)
            raw = Prompt.ask("Группа или команда").strip()
            key = raw.casefold()
            if key == "0":
                console.print("Работа завершена.")
                return
            if key in commands:
                commands[key]()
                continue
            if key == "сохранить":
                paths = save_reports(dataset, Path("reports"))
                console.print(f"[green]Записано файлов: {len(paths)}[/green]")
                for path in paths:
                    console.print(f"  {path}")
                _pause(console)
                continue
            group = _resolve_group(dataset, raw)
            if group is None:
                console.print("[red]Нет такой группы или команды.[/red]")
                _pause(console)
                continue
            browse_group(console, dataset, group)
    except (KeyboardInterrupt, EOFError):
        console.print("\nВыход.")
