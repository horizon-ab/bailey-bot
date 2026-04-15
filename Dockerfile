FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	&& rm -rf /var/lib/apt/lists/*

COPY bot-requirements.txt .
COPY model/model-requirements.txt model/model-requirements.txt
RUN pip install --no-cache-dir -r bot-requirements.txt
RUN pip install --no-cache-dir -r model/model-requirements.txt

COPY . . 

RUN touch config.json

CMD ["python", "bot.py"]

