FROM python:3.12-slim

ENV GIT_REPO=https://github.com/marstion/telegram_message_forward.git

VOLUME /app/sessions

WORKDIR /app

RUN apt update && apt install git -y && git clone $GIT_REPO . && pip install --no-cache-dir -r requirements.txt && rm -rf /var/lib/apt /var/cache/apt

CMD ["python", "main.py"]
