#!/bin/bash
# sh restore.sh -e dev -u michal -d ctdb
# restore postgres database from last backup

while getopts e:u:d: option
do
case "${option}"
in
e) ENV=${OPTARG};;
u) USER=${OPTARG};;
d) DB=${OPTARG};;
esac
done

postgres_container_id="$(docker container ls | grep -i 'postgres' | sed -e 's/^\(.\{12\}\).*/\1/')"

if [ $postgres_container_id ]
then
	echo "\nPostgres container id: ${postgres_container_id}"
	if [ "$ENV" = "prod" ]
	then
		last_backup_file="$(ls backups -t | grep -i 'prod' | head -n1)"
	else
		last_backup_file="$(ls backups -t | grep -i 'dev' | head -n1)"	
	fi

	cat backups/$last_backup_file | docker exec -i $postgres_container_id psql -d ctdbdev -U michal
	
	if [ "$ENV" = "prod" ]
	then
		new_backup_file="$(ls backups -t | grep -i 'prod' | head -n1)"
	else
		new_backup_file="$(ls backups -t | grep -i 'dev' | head -n1)"	
	fi

	echo "\nDatabase has been restored from: \nbackups/${new_backup_file}\n"
else
	echo "Postgres container not found"
fi

