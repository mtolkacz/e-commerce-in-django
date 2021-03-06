#!/bin/bash
while getopts e: option
do
case "${option}"
in
e) ENV=${OPTARG};;
esac
done

key=""

# echo "\nThis command will restore database. Ctrl + C to cancel, any key to start"
# read key

if [ "$ENV" = "prod" ]
then
  # docker-compose -f $(dirname $PWD)/production.yml up -d
  sleep 10
  # sh $(dirname $PWD)/scripts/restore.sh -e prod -u michal -d ctdb
elif [ "$ENV" = "dev" ]
then
  docker-compose -f $(dirname $PWD)/local.yml up -d
  # sleep 10
  # sh $(dirname $PWD)/scripts/restore.sh -e dev -u michal -d ctdbdev
else
  echo "Incorrect environment"
fi
