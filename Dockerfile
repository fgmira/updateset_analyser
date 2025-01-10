FROM python:3.12

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock entrypoint.sh ./
COPY ./updateset_analyser ./updateset_analyser

RUN poetry install --no-root
RUN poetry add opentelemetry-distro
RUN poetry add opentelemetry-exporter-otlp-proto-grpc

RUN poetry run opentelemetry-bootstrap -a install
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]




