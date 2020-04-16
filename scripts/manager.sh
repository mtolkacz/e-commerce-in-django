#!/bin/bash

enter="" 
number=-1

# helpful commands
commands=" 
\ndocker-compose up -d --build web
\ndocker container ls
\ndocker-compose exec web python manage.py makemigrations
\ndocker-compose exec web python manage.py migrate
\nsh backup.sh -e dev -u michal -d ctdb
\nsh restore.sh -e dev -u michal -d ctdb
\ndocker-compose exec web python manage.py shell
\ndocker-compose exec web python manage.py createsuperuser
\ndocker network ls
\ndocker network inspect gallop | grep 'Name\|IPv4'
\ndocker-compose exec web pip list
\ngnome-terminal
\ndocker-compose logs --tail=\"100\" | grep -Ev \"Found another file|pgadmin|elasticsearch\"
\ndocker ps --format \"{{.Names}}\" | grep -i \"pgadmin\" - name of container for pgadmin
\ndocker image prune -a - clean up unused images
\ndocker container prune - clean up unused containers
\ndocker network inspect gallop_default
\ndocker network rm gallop_default
\ndocker network rm gallop
\ndocker swarm init
\ndocker network create -d bridge --subnet=172.18.0.0/16 gallop
\ndocker swarm leave --force"

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
	echo "\nChoose: "
    read number
    case "$number" in
	1)  sh start.sh
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
	7)  sh backup.sh -e dev -u michal -d ctdb
	   ;;
	8)  sh restore.sh -e dev -u michal -d ctdb
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
	0) exit 0
	   ;;
	*) echo
	   ;;
	esac
	echo "\nPress any key..."
	read enter	
	clear
done
