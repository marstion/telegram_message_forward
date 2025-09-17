FROM python:3.12-slim

VOLUME /app/sessions

WORKDIR /app

ADD . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]