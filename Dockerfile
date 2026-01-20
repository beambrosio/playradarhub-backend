FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TWITCH_CLIENT_ID=${TWITCH_CLIENT_ID}
ENV TWITCH_CLIENT_SECRET=${TWITCH_CLIENT_SECRET}


EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]