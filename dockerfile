FROM python:3.11-slim

WORKDIR /app

USER root
COPY requirements.txt requirements.txt
COPY main.py main.py
COPY model.pkl model.pkl
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system lcapi && adduser --system --ingroup lcapi lcapi
RUN chown -R lcapi:lcapi /app
USER lcapi

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
