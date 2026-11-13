FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY attendance ./attendance
COPY tests ./tests
COPY students.json .
COPY journal.xlsx .
COPY kontrol_poseshchaemosti.py .
COPY README.md .

RUN python -m pytest -q

ENTRYPOINT ["python", "kontrol_poseshchaemosti.py"]
