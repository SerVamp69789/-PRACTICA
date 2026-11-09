import json, os

ФАЙЛ = "attendance_data.json"

class Система:
    def __init__(self):
        self.студенты, self.посещаемость = {}, []

    def загрузить(self):
        if not os.path.exists(ФАЙЛ):
            return False
        with open(ФАЙЛ, encoding="utf-8") as f:
            d = json.load(f)
        self.студенты, self.посещаемость = d["студенты"], d["посещаемость"]
        return True

    def сохранить(self):
        with open(ФАЙЛ, "w", encoding="utf-8") as f:
            json.dump({"студенты": self.студенты, "посещаемость": self.посещаемость},
                      f, ensure_ascii=False, indent=2)

    def посещаемость_студента(self, sid):
        recs = [r for r in self.посещаемость if r["студент_id"] == sid]
        return (100 * sum(r["присутствовал"] for r in recs) / len(recs), len(recs)) \
               if recs else (100.0, 0)

    def все_группы(self):
        return sorted({v["группа"] for v in self.студенты.values()})

def сводка(система):
    print(f"\n{'═' * 64}\nСВОДКА ПО ГРУППАМ И СТУДЕНТАМ\n{'═' * 64}")
    if not система.студенты:
        print("  Данных нет.")
        return
    for g in система.все_группы():
        ids = sorted((s for s, v in система.студенты.items() if v["группа"] == g),
                     key=lambda s: система.посещаемость_студента(s)[0], reverse=True)
        avg = sum(система.посещаемость_студента(s)[0] for s in ids) / len(ids)
        print(f"\n  {g} — студентов: {len(ids)}, средняя посещаемость: {avg:.1f}%")
        print(f"    {'ФИО':<34}{'Занятий':>8}{'Посещаемость':>15}\n    {'-' * 57}")
        for sid in ids:
            pct, всего = система.посещаемость_студента(sid)
            print(f"    {система.студенты[sid]['фио']:<34}{всего:>8}{pct:>15.1f}%")

МЕНЮ = """══════════════════════════════════════════════
  КОНТРОЛЬ ПОСЕЩАЕМОСТИ — АДМИН-КОНСОЛЬ
══════════════════════════════════════════════
 1 — Сводка по группам и студентам
 0 — Сохранить и выйти"""

def главная():
    система = Система()
    if система.загрузить():
        print(f"Данные загружены: {len(система.студенты)} студентов, {len(система.посещаемость)} отметок.")
    else:
        print("Файл attendance_data.json не найден.")
    while True:
        print(МЕНЮ)
        ch = input("Ваш выбор: ").strip()
        if ch == "1":
            сводка(система)
        elif ch == "0":
            система.сохранить()
            print("Данные сохранены. До встречи!")
            break
        else:
            print("Выберите 1 или 0.")


if __name__ == "__main__":
    главная()
