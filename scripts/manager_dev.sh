#!/bin/bash

enter="" 
number=-1

# helpful commands
commands="$(cat commands.txt)"

while [ ! $number -eq 0 ]; do
	clear
	echo "1.up containers"
	echo "2.stop containters"
	echo "3.build web container"
	echo "4.status of containers"
	echo "5.makemigration"
	echo "6.migrate"
	echo "7.backup"
	echo "8.restore"
	echo "9.shell"
	echo "10.superuser"
	echo "11.container networks"
	echo "12.container network IP "
	echo "13.pip list"
	echo "14.git status"
	echo "15.open new terminal"
	echo "16.last 100 container logs (without elasticsearch and pgadmin)"
	echo "17.display commands"
	echo "18.down containers"
	echo "19.cleanup unused images"
	echo "20.cleanup unused container"
	echo "21.gallop network detail"
	echo "22.django test"
	echo "23.clear expired sessions"
	echo "24.project backup"
        echo "25.celery log"
        echo "26.web log"
	echo "27.redis log"
 	echo "28.redis container IP"
        echo "29.celery mail"
        echo "30.build celery container"
	echo "31.db container ip"
	echo "32.elasticsearch container log"
	echo "33.rebuild indexes"
	echo "34.kazen"
	printf "\nChoose: "
    read number
    case "$number" in
	1)  sh $(dirname $PWD)/start.sh -e dev
	    ;;
	2)  docker-compose stop
	    ;;
	3)  docker-compose up -d --build web
	    ;;
	4)  docker container ls
	   ;;
	5)  docker-compose exec web python manage.py makemigrations
	   ;;
	6)  docker-compose exec web python manage.py migrate
	   ;;
	7)  sh backup.sh -e dev -u michal
	   ;;
	8)  sh restore.sh -e dev -u michal -d ctdbdev
	   ;;
	9)  docker-compose exec web python manage.py shell
	   ;;
	10) docker-compose exec web python manage.py createsuperuser
	   ;;
	11) docker network ls
	   ;;
	12) docker network inspect gallop | grep 'Name\|IPv4'
	   ;;
	13) docker-compose exec web pip list
	   ;;
	14) git status
	   ;;
  	15) gnome-terminal
	   ;;	
	16) docker-compose logs --tail="100" | grep -Ev "Found another file|pgadmin|elasticsearch"
	   ;;
	17) echo $commands
	   ;;
	18) docker-compose down -v
	   ;;
	19) docker image prune -a
	   ;;
	20) docker container prune
	   ;;
	21) docker network inspect gallop
	   ;;
	22) docker-compose logs --tail="100" | grep -E "DJANGOTEST:"
	   ;;
	23) docker-compose exec web python manage.py clearsessions
	   ;;
	24) cp -r /home/michal/MEGAsync/GitHub/gallop '/home/michal/MEGAsync/GitHub/gallop backup/gallop_'`date +'%d-%m-%Y_%H_%M_%S'`
	   ;;
	25) docker-compose logs --tail="100" | grep -E "celery"
	   ;;
	26) docker-compose logs --tail="100" | grep -E "web"
	   ;;
	27) docker-compose logs --tail="100" | grep -E "redis"
	   ;;
	28) docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gallop_redis_1
	   ;;
	29) docker-compose logs --tail="100" | grep -E "mail"
           ;;
	30) docker-compose up -d --build celery | docker-compose up -d --build celery-beat
           ;;
	31) docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gallop_db
	   ;;
	32) docker-compose logs --tail="100" | grep -E "elastic"
	   ;;
	33) docker-compose exec web python manage.py search_index --rebuild
	   ;;
	34) gnome-terminal -- sudo "$(dirname $PWD)"/kaizen/jre/bin/java -jar "$(dirname $PWD)"/kaizen/kaizen.jar -Xms128M -Xmx2g
	   ;;
	0) exit 0
	   ;;
	*) echo
	   ;;
	esac
	printf "\nPress any key..."
	read enter	
	clear
done
