FROM python:3.10-slim

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
COPY ./requirements ./requirements
RUN apt-get update
RUN apt-get install -y default-mysql-client
RUN pip install --no-cache-dir --upgrade -r ./requirements/common.txt

COPY ./src ./src
COPY ./client ./client
COPY ./main.py ./
COPY ./.env.dev ./
COPY ./images ./images
COPY ./json ./json
COPY ./mysql/migrations ./mysql/migrations
COPY ./alembic.ini ./alembic.ini

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONOPTIMIZE 2

CMD ["python", "main.py"]