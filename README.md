# E-commerce in django

## Project name
gallop

## Purpose
e-commerce system

## Technologies

###### backend and environment
- docker compose 3.3
- python 3.8
- django 2.2.10
- django-sslserver
- postgres 12.2
- redis-server 6.0.1
- rabbitmq 3.8.3
- celery 4.4.2
- pgadmin4
- nginx 1.17.2
- gunicorn 19.9.0
- elasticsearch2
- Facebook/Twitter authentication

###### frontend
- HTML5
- jQuery 2.2.4
- bootstrap4


## Installation Guide

**Create environment files for docker compose and assigned value to following variables**
###### prod<br>
- .env <br>
- .env.db <br>

###### dev 
- .envdev
```
SECRET_KEY
DEBUG
SQL_USER
SQL_PASSWORD
SQL_DATABASE
SQL_HOST
SQL_PORT
EMAIL_HOST
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_PORT
SOCIAL_AUTH_FACEBOOK_KEY
SOCIAL_AUTH_FACEBOOK_SECRET
SOCIAL_AUTH_TWITTER_KEY
SOCIAL_AUTH_TWITTER_SECRET
```
- .envdevdb
```
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
```
- .pgadmindev
```
PGADMIN_DEFAULT_EMAIL
PGADMIN_DEFAULT_PASSWORD
PGADMIN_LISTEN_PORT
```

**Running docker**
###### prod<br>
`docker-compose -f docker-compose.prod.yml up --build`<br>
###### dev<br>
`docker-compose up  --build`<br><br>

**Migrating django models**<br><br>
`docker-compose exec web python manage.py makemigrations`<br>
`docker-compose exec web python manage.py migrate`
<br><br>
> There's possibility to add automigration e.g. in entrypoint.sh (entrypoint.prod.sh)

<br>**Creating superuser**<br><br>
`docker-compose exec web python manage.py createsuperuser`
<br><br>
**Bash postgres database backup and restore scripts (if you've done django migration already)**
###### backup <br>
`sh backup.sh -e {choose env: dev/prod} -u {POSTGRES_USER} -d {POSTGRES_DB}` <br>

###### restore <br>
`sh restore.sh -e {choose env: dev/prod} -u {POSTGRES_USER} -d {POSTGRES_DB}` <br>
<br>
> ###### examples:<br>
> `sh backup.sh -e dev -u michal -d ctdbdev` <br>
> `sh backup.sh -e prod -u michal -d ctdb` <br>
> `sh restore.sh -e dev -u michal -d ctdbdev` <br>
> `sh restore.sh -e prod -u michal -d ctdb` 

<br>**Connecting to pgadmin4 on localhost**
###### Use IPv4 address from postgres docker container to connect to postgres database <br>
`docker network inspect {your_container_network_name} | grep 'Name\|IPv4'` <br><br>
> ###### Example:<br>
> `docker network inspect gallop_default | grep 'Name\|IPv4'`

