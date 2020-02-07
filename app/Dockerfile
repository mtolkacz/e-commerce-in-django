FROM python:3.7.4-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add --no-cache --virtual build-deps gcc python3-dev musl-dev build-base linux-headers \
    && apk add postgresql-dev \ 
    && apk add --no-cache jpeg-dev zlib-dev libjpeg \
    && pip install --upgrade pip \
    && pip install psycopg2 Pillow django-sslserver>=0.21 \
    && apk del build-deps 

RUN pip install --upgrade pip
RUN pip install pipenv
COPY ./Pipfile /usr/src/app/Pipfile
RUN pipenv install --skip-lock --system --dev

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

COPY . /usr/src/app

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
