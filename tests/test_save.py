"""Запись отчётов в папку: сводка, стипендия, отчисление и файл каждой группы."""

from attendance.reports import report_bundle
from attendance.storage import load_dataset
from attendance.ui import save_reports
from pathlib import Path


def test_save_writes_college_and_group_files(tmp_path: Path):
    dataset = load_dataset(Path(__file__).resolve().parents[1] / "students.json")
    written = save_reports(dataset, tmp_path)
    names = {path.name for path in written}
    assert names == set(report_bundle(dataset))
    assert "сводный-отчёт.txt" in names
    assert "лишение-стипендии.txt" in names
    assert "отчисление.txt" in names
    assert "группа-2ИП-2-25.txt" in names
    text = (tmp_path / "отчисление.txt").read_text(encoding="utf-8")
    assert "Фомин Юрий Ильич" in text
