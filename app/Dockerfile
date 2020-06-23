FROM python:3.8

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y netcat
RUN pip install --upgrade pip
RUN pip install pipenv psycopg2==2.8.4 Pillow==5.3.0 django-sslserver==0.21 
COPY ./Pipfile /usr/src/app/Pipfile
RUN pipenv install --skip-lock --system --dev

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

COPY . /usr/src/app

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
