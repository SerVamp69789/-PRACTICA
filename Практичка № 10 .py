import json
from collections import defaultdict

def load_data(filename):
    """Загружает данные из JSON-файла."""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def calculate_attendance(data):
    """
    Вычисляет процент посещаемости для каждого студента.
    Возвращает список кортежей: (ФИО, группа, всего, посещено, процент).
    """
    students = data.get('студенты', {})
    attendance = data.get('посещаемость', [])

    # Счётчики: для каждого студента — [всего записей, посещено]
    stats = defaultdict(lambda: [0, 0])

    for record in attendance:
        student_id = record.get('студент_id')
        if student_id is None:
            continue
        stats[student_id][0] += 1
        if record.get('присутствовал'):
            stats[student_id][1] += 1

    result = []
    for student_id, info in students.items():
        total, present = stats.get(student_id, [0, 0])
        percent = (present / total * 100) if total > 0 else 0.0
        result.append((
            info.get('фио', '—'),
            info.get('группа', '—'),
            total,
            present,
            percent,
        ))

    # Сортировка по группе и ФИО
    result.sort(key=lambda x: (x[1], x[0]))
    return result

def print_table(rows):
    """Выводит результаты в табличной форме."""
    if not rows:
        print("Нет данных для отображения.")
        return

    headers = ['ФИО', 'Группа', 'Всего', 'Посещено', 'Процент']
    # Ширина колонок
    widths = [max(len(str(h)), max(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)]

    # Форматирование строк
    def format_row(values):
        return ' | '.join(str(v).ljust(widths[i]) for i, v in enumerate(values))

    separator = '-+-'.join('-' * w for w in widths)

    print(format_row(headers))
    print(separator)
    for row in rows:
        # Процент с одним знаком после запятой
        display = list(row[:4]) + [f"{row[4]:.1f}%"]
        print(format_row(display))
    print(separator)

def main(filename='students.json'):
    data = load_data(filename)
    rows = calculate_attendance(data)
    print_table(rows)

if __name__ == '__main__':
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else 'students.json'
    main(filename)
