FROM python:3.13

RUN pip install --no-cache-dir poetry

WORKDIR /code
COPY pyproject.toml poetry.lock* /code/

RUN poetry install --no-interaction --no-ansi

COPY ./app /code/app

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
