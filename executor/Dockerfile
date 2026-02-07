FROM python:3.14.3-slim-trixie

RUN pip install uvicorn[standard] fastapi websockets pexpect

WORKDIR /app
ENV PYTHONUNBUFFERED 1
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]