"""Расшифровка кода учебной группы."""

import re

SPECIALTIES = {
    "ИП": "Информационные системы и программирование",
    "РКИ": "Разработка компьютерных игр и дополненной виртуальной реальности",
}

_CODE = re.compile(r"^(\d+)([А-ЯЁ]+)-(\d+)-(\d{2})$")


def describe_group(code: str) -> str:
    """Purpose: превратить код группы в понятную строку для экрана.
    Inputs: code — шифр вроде 2ИП-2-25 или 2РКИ-1-25.
    Output: «2 курс группа 2 … 2025 г». Если шифр незнакомый, возвращает его как есть.
    Why: первая цифра — курс, буквы — специальность, вторая цифра — номер группы, последние две — год поступления.
    """
    match = _CODE.match(code.strip())
    if match is None:
        return code
    # 2ИП-2-25: курс 2, специальность ИП, группа 2, поступление в 2025 году.
    course, specialty, number, year = match.groups()
    title = SPECIALTIES.get(specialty, specialty)
    return f"{int(course)} курс группа {int(number)} {title} {2000 + int(year)} г"
