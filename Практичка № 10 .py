import json, os
FILENAME = "attendance_data.json"

class AttendanceSystem:
    def __init__(self):
        self.students, self.attendance_records = {}, []

    def load(self):
        if not os.path.exists(FILENAME): return False
        with open(FILENAME, encoding="utf-8") as f:
            d = json.load(f)
        self.students = d.get("students", {})
        self.attendance_records = d.get("attendance", [])
        return True

    def save(self):
        with open(FILENAME, "w", encoding="utf-8") as f:
            json.dump({"students": self.students, "attendance": self.attendance_records}, f, ensure_ascii=False, indent=2)

    def get_student_attendance(self, sid):
        recs = [r for r in self.attendance_records if r["student_id"] == sid]
        if not recs: return 100.0, 0
        return 100 * sum(r["present"] for r in recs) / len(recs), len(recs)

    def get_all_groups(self):
        return sorted({s["group"] for s in self.students.values()})

def print_summary(system):
    print("\n" + "=" * 64)
    print("КОНТРОЛЬ ПОСЕЩАЕМОСТИ — СВОДКА ПО ГРУППАМ И СТУДЕНТАМ")
    print("=" * 64)
    if not system.students:
        print("  Данных нет.")
        return
    for g in system.get_all_groups():
        ids = sorted((sid for sid, v in system.students.items() if v["group"] == g),
                     key=lambda s: system.get_student_attendance(s)[0], reverse=True)
        avg = sum(system.get_student_attendance(s)[0] for s in ids) / len(ids)
        print(f"\n  {g} — студентов: {len(ids)}, средняя посещаемость: {avg:.1f}%")
        print(f"    {'ФИО':<34}{'Занятий':>8}{'Посещаемость':>15}\n    {'-' * 57}")
        for sid in ids:
            pct, total = system.get_student_attendance(sid)
            print(f"    {system.students[sid]['full_name']:<34}{total:>8}{pct:>15.1f}%")

MENU = """
================================================================
  КОНТРОЛЬ ПОСЕЩАЕМОСТИ — АДМИН-КОНСОЛЬ
================================================================
 1 — Сводка по группам и студентам
 0 — Сохранить и выйти"""

def main():
    system = AttendanceSystem()
    if system.load():
        print(f"Данные загружены: {len(system.students)} студентов, {len(system.attendance_records)} отметок.")
    else:
        print("Файл attendance_data.json не найден.")
    while True:
        print(MENU)
        ch = input("Ваш выбор: ").strip()
        if ch == "1":
            print_summary(system)
        elif ch == "0":
            system.save()
            print("Данные сохранены. До встречи!")
            break
        else:
            print("Выберите 1 или 0.")

if __name__ == "__main__":
    main()
