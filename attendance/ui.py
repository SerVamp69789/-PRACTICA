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


def _bar(percent: float, width: int = 10) -> str:
    filled = round(percent / 100 * width)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def _status_text(status: str) -> Text:
    return Text(STATUS_LABELS[status], style=STATUS_STYLE[status])


def _pause(console: Console) -> None:
    Prompt.ask("\n[dim]Enter — назад[/dim]", default="", show_default=False)


def render_home(console: Console, dataset: Dataset) -> None:
    """Purpose: главный экран со сводкой колледжа и пунктами меню.
    Inputs: console — вывод rich, dataset — журнал.
    Output: ничего, рисует панель.
    Why: администратор сразу видит масштаб проблемы, ещё не открывая группу.
    """
    summary = college_summary(dataset)
    headline = Text()
    headline.append("ДЕКАНАТ", style="bold cyan")
    headline.append("  ·  контроль посещаемости\n", style="white")
    headline.append(f"Журнал {dataset.source_name}", style="dim")
    headline.append(
        f"   ·   групп {len(summary.groups)}   ·   студентов {summary.headcount}\n",
        style="white",
    )
    headline.append(f"Пропуски {_bar(summary.absence_percent)}  {summary.absence_percent:.1f}%", style="cyan")
    headline.append(
        f"    отстающие {summary.lagging}    стипендия {summary.scholarship}    отчисление {summary.expulsion}",
        style="white",
    )
    console.print(Panel(headline, box=box.ROUNDED, border_style="cyan", padding=(1, 2)))
    menu = Table.grid(padding=(0, 2))
    menu.add_column(style="bold cyan", justify="right")
    menu.add_column()
    items = [
        ("1", "Группы колледжа"),
        ("2", "Группа и список студентов"),
        ("3", "Сводный отчёт"),
        ("4", "Отстающие студенты"),
        ("5", "Отчёт на лишение стипендии"),
        ("6", "Отчёт на отчисление"),
        ("7", "Сохранить отчёты в reports/"),
        ("0", "Выход"),
    ]
    for key, label in items:
        menu.add_row(key, label)
    console.print(Panel(menu, title="Меню", border_style="bright_black"))


def _groups_table(dataset: Dataset) -> Table:
    summary = college_summary(dataset)
    table = Table(
        title="Группы",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("№", justify="right", style="dim")
    table.add_column("Группа", style="bold")
    table.add_column("Студентов", justify="right")
    table.add_column("Пропусков", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Шкала")
    table.add_column("Внимание", justify="right")
    table.add_column("Стипендия", justify="right")
    table.add_column("Отчисление", justify="right")
    for index, group in enumerate(summary.groups, start=1):
        table.add_row(
            str(index),
            group.code,
            str(group.headcount),
            f"{group.absences}/{group.lessons_total}",
            f"{group.absence_percent:.1f}",
            _bar(group.absence_percent),
            str(group.attention),
            str(group.scholarship),
            str(group.expulsion),
        )
    return table


def _students_table(group: GroupSummary, dataset: Dataset) -> Table:
    table = Table(
        title=f"{group.code}  ·  пропуски {group.absence_percent:.1f}%  ·  {group.headcount} студентов",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("№", justify="right", style="dim")
    table.add_column("Студент")
    table.add_column("Был", justify="right")
    table.add_column("Пропусков", justify="right")
    table.add_column("%", justify="right")
    table.add_column("Шкала")
    table.add_column("Статус")
    for index, student in enumerate(group.students, start=1):
        status = classify(student.absence_percent, dataset.rules)
        table.add_row(
            str(index),
            student.full_name,
            str(student.presents),
            f"{student.absences}/{student.lessons_total}",
            f"{student.absence_percent:.1f}",
            _bar(student.absence_percent),
            _status_text(status),
        )
    return table


def _resolve_group(dataset: Dataset, raw: str) -> GroupSummary | None:
    groups = college_summary(dataset).groups
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
        console.clear()
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


def browse_groups(console: Console, dataset: Dataset) -> None:
    """Purpose: экран списка групп и переход в выбранную.
    Inputs: console, dataset.
    Output: ничего.
    Why: вход в систему для администратора — обзор групп, а не плоский список всех людей.
    """
    while True:
        console.clear()
        console.print(_groups_table(dataset))
        raw = Prompt.ask("Номер или код группы, 0 — в меню").strip()
        if raw == "0":
            return
        group = _resolve_group(dataset, raw)
        if group is None:
            console.print("[red]Такой группы нет.[/red]")
            _pause(console)
            continue
        browse_group(console, dataset, group)


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
    """Purpose: цикл главного меню.
    Inputs: dataset — загруженный журнал.
    Output: ничего, завершается по пункту «Выход» или Ctrl+C.
    Why: это рабочее место администратора, а не одноразовый вывод таблицы.
    """
    console = Console()
    try:
        while True:
            console.clear()
            render_home(console, dataset)
            choice = Prompt.ask("Пункт", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="1")
            if choice == "0":
                console.print("Работа завершена.")
                return
            if choice in {"1", "2"}:
                browse_groups(console, dataset)
            elif choice == "3":
                _show_text(console, "Сводный отчёт", format_college(dataset))
            elif choice == "4":
                _show_text(console, "Отстающие", format_lagging(dataset))
            elif choice == "5":
                _show_text(console, "Лишение стипендии", format_scholarship(dataset))
            elif choice == "6":
                _show_text(console, "Отчисление", format_expulsion(dataset))
            elif choice == "7":
                paths = save_reports(dataset, Path("reports"))
                console.print(f"[green]Записано файлов: {len(paths)}[/green]")
                for path in paths:
                    console.print(f"  {path}")
                _pause(console)
    except (KeyboardInterrupt, EOFError):
        console.print("\nВыход.")
