"""Система контроля посещаемости.

Аналитическая консоль для администрации колледжа.
Агрегирует журнал по всем группам, считает процент пропусков
и формирует сводные административные отчёты: отстающие,
лишение стипендии, отчисление.

На экране сразу список групп. Номер или код группы открывает
список её студентов. Команды сводка, отстающие, стипендия,
отчисление и сохранить дают отчёты по всему заведению.

Журнал — students.json. Запуск: python kontrol_poseshchaemosti.py
"""

import argparse
import sys
from pathlib import Path

from attendance.analytics import JournalError, college_summary
from attendance.reports import (
    format_college,
    format_expulsion,
    format_group,
    format_lagging,
    format_scholarship,
)
from attendance.storage import load_dataset
from attendance.ui import run_menu, save_reports

REPORTS = {
    "summary": format_college,
    "lagging": format_lagging,
    "scholarship": format_scholarship,
    "expulsion": format_expulsion,
}


def build_parser() -> argparse.ArgumentParser:
    """Purpose: описать аргументы командной строки.
    Inputs: нет.
    Output: настроенный парсер.
    Why: меню нужно человеку, а отчёт без вопросов нужен Docker и проверке.
    """
    parser = argparse.ArgumentParser(
        description="Система контроля посещаемости: группы, процент пропусков, административные отчёты"
    )
    parser.add_argument("--data", default="students.json", help="Путь к журналу JSON")
    parser.add_argument("--report", choices=sorted(REPORTS), help="Напечатать отчёт и выйти")
    parser.add_argument("--group", help="Напечатать список студентов группы и выйти")
    parser.add_argument("--save", action="store_true", help="Сохранить отчёты в reports/ и выйти")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Purpose: загрузить журнал и открыть меню либо разовый отчёт.
    Inputs: argv — аргументы без имени программы; по умолчанию берутся из командной строки.
    Output: код возврата 0 при успехе, 1 при ошибке журнала или неизвестной группе.
    Why: и человек, и Docker запускают один и тот же файл.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        dataset = load_dataset(Path(args.data))
    except JournalError as error:
        print(error, file=sys.stderr)
        return 1

    # Без меню: одна группа, один отчёт или запись файлов. Иначе открывается экран.
    if args.group:
        match = next((group for group in college_summary(dataset).groups if group.code == args.group), None)
        if match is None:
            print(f"Группа не найдена: {args.group}", file=sys.stderr)
            return 1
        print(format_group(match, dataset))
        return 0
    if args.report:
        print(REPORTS[args.report](dataset))
        return 0
    if args.save:
        paths = save_reports(dataset, Path("reports"))
        for path in paths:
            print(path)
        return 0
    run_menu(dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
