FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=offscreen

COPY requirements.txt pyproject.toml README.md ./
COPY masterblaster_control ./masterblaster_control
COPY scripts ./scripts
COPY tests ./tests
COPY main.py ./

RUN pip install --no-cache-dir -r requirements.txt

RUN python scripts/validate_p0_registry.py
RUN python -m pytest -q

CMD ["python", "scripts/demo_p0_overdrive.py"]