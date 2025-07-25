FROM python:3.13.5-alpine3.22

WORKDIR /app

USER root
COPY . .s
USER lcapi

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
