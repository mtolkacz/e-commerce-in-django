#!/bin/bash
# sh backup.sh -e dev -u michal -d ctdb
# create backup of docker postgres database

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

	# get latest file of last backup
	if [ "$ENV" = "prod" ]
	then
		last_backup_file="$(ls backups -t | grep -i 'prod' | head -n1)"
	else
		last_backup_file="$(ls backups -t | grep -i 'dev' | head -n1)"	
	fi
	project="$(basename $PWD)"
	
	mkdir -p backups

	docker exec -t $postgres_container_id pg_dumpall -c -U $USER > backups/${project}_${ENV}_`date +%d-%m-%Y_%H_%M_%S`.sql
	if [ "$ENV" = "prod" ]
	then
		new_backup_file="$(ls backups -t | grep -i 'prod' | head -n1)"
	else
		new_backup_file="$(ls backups -t | grep -i 'dev' | head -n1)"	
	fi
	if [ $last_backup_file != $new_backup_file ]
	then
		echo "\nBackup has been created: \nbackups/${new_backup_file}\n"
	else
		echo "\nBackup has not been created\n"
	fi

else
	echo "Postgres container not found"
fi
