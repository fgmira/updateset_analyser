#!/bin/bash

cd updateset_analyser

if [ "$START_MODE" = "api" ]; then
    echo "Starting API"
    exec poetry run opentelemetry-instrument --logs_exporter console,otlp uvicorn app:app --host 0.0.0.0 --port 8000 --log-level $LOG_LEVEL
elif [ "$START_MODE" = "worker" ]; then
    echo "Starting Worker"
    exec poetry run opentelemetry-instrument --logs_exporter console,otlp celery -A tasks worker --loglevel=$LOG_LEVEL
else
    echo "Unknown START_MODE: $START_MODE"
    exit 1
fi