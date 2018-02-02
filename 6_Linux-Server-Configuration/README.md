# Linux-Server-Configuration
Visit http://ec2-52-221-120-50.ap-southeast-1.compute.amazonaws.com for the demonstration of the Project
Server Public IP address: `52.221.120.50`


## Security
### Change the SSH port from 22 to 2200
1. Change `Port 22` to `Port 2200` in `/etc/ssh/sshd_config`
	
		sudo vim /etc/ssh/sshd_config
2. Restart ssh service

		sudo service ssh restart

### Configure the Uncomplicated Firewall
- Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for `SSH (port 2200)`, `HTTP (port 80)`, and `NTP (port 123)`

		sudo ufw allow 2200/tcp
		sudo ufw allow 80/tcp
		sudo ufw allow 123/udp
		sudo ufw enable

### Enforce ssh authentication
1. Change `PasswordAuthentication yes` into  `PasswordAuthentication no`

		sudo vim /etc/ssh/sshd_config
2. Restart ssh service

		sudo service ssh restart


## User Management
### Create a new user named `grader`
	sudo adduser grader

### Grant `grader` sudo permission
`sudo vim /etc/sudoers.d/grader`
		
		grader ALL=(ALL) ALL

### Setup `grader` public-key
1. On local machine 

		ssh-keygen -t rsa
	- Choose the default folder

			~/.ssh/id_rsa.pub
			~/.ssh/id_rsa
2. Setup public key for `grader` on server
	- Copy the content of the public key on the local machine `~/.ssh/id_rsa.pub` into `/home/grader/.ssh/authorized_keys`

			sudo mkdir /home/grader/.ssh
			sudo vim /home/grader/.ssh/authorized_keys

	
3. Grant access permissions

		sudo chmod 700 /home/grader/.ssh
		sudo chmod 644 /home/grader/.ssh/authorized_keys
4. Restart ssh service

		sudo service ssh restart

5. Now `grader` can login through ssh service

		ssh grader@52.221.120.50 -p 2200 -i ~/.ssh/id_rsa

### Disable Root login
1 Change `PermitRootLogin prohibit-password` into  `PermitRootLogin no`

		sudo vim /etc/ssh/sshd_config
2. Restart ssh service

		sudo service ssh restart


## Deploy the Build-an-Item-Catalog Flask Web Application to Amazon Lightsail server
### Install all necessary packages
	sudo apt-get update
	sudo apt-get install -y git apache2 libapache2-mod-wsgi python-dev python-pip

### Install virtual environment package
	sudo pip install virtualenv

### Enable wsgi
	sudo a2enmod wsgi

### Configure the application
1. Clone the Project

		cd /var/www
		sudo git clone https://github.com/dangkhoa1992/Build-an-Item-Catalog.git
2. Delete `.git`

		cd /var/www/Build-an-Item-Catalog
		sudo rm -rf .git
3. Rename `webserver.py`

		cd /var/www/Build-an-Item-Catalog/ItemCatalog
		sudo mv webserver.py __init__.py
4. Change from sqlite to postgresql
	- Edit `__init__.py`, `DBsetup.py` and `addItems.py` and change `engine = create_engine('sqlite:///categories.db')` into `engine = create_engine('postgresql://admin:abc123@localhost/catalog')`
5. Set absolute directory link to `client_secrets.json` file
	- Edit `__init__.py` and change `open('client_secrets.json', 'r')` into 
		`open('/var/www/Build-an-Item-Catalog/ItemCatalog/client_secrets.json', 'r')`,
		`flow_from_clientsecrets('client_secrets.json', scope='')` into 
		`flow_from_clientsecrets('/var/www/Build-an-Item-Catalog/ItemCatalog/client_secrets.json', scope='')`
6. Update OAth2 API
	- Go to https://console.developers.google.com and update the Client secret then download the new client_secrets.json

### Create and Configure a postgresql database
1. Install postgresql

		sudo apt-get -qqy install postgresql python-psycopg2
2. Login as user `postgres`

		cd /var/www/Build-an-Item-Catalog/ItemCatalog
		sudo su - postgres
3. Get into postgreSQL shell

		psql
4. Create a new database named `catalog`

		CREATE DATABASE catalog;
5. Create a user named `admin`

		CREATE USER admin;
6. Set a password for the user

		ALTER ROLE admin WITH PASSWORD 'abc123';
7. Give `admin` user permission to update `catalog` application database

		GRANT ALL PRIVILEGES ON DATABASE catalog TO admin;
8. quit postgreSQL

		\q
9. Exit from user `postgres`

		exit

### Create and Configure a Virtual Environment
1. Create a virtual environment

		cd /var/www/Build-an-Item-Catalog/ItemCatalog
		sudo virtualenv venv
2. Activate virtual environment

		source venv/bin/activate
3. Install all necessary packages for the project

		sudo pip install -r requirements.txt
4. Create database schema

		sudo python DBsetup.py
5. Add prebuilt items (Optional)

		sudo python addItems.py
6. Deactivate virtual environment

		deactivate

### Create and Configure a virtual host
1. Create a conf file `sudo vim /etc/apache2/sites-available/Build-an-Item-Catalog.conf`

		<VirtualHost *:80>
			ServerName http://ec2-52-221-120-50.ap-southeast-1.compute.amazonaws.com/
			ServerAdmin dangledangkhoa@gmail.com
			WSGIScriptAlias / /var/www/Build-an-Item-Catalog/catalog.wsgi
			<Directory /var/www/Build-an-Item-Catalog/ItemCatalog/>
				Order allow,deny
				Allow from all
			</Directory>
			Alias /static /var/www/Build-an-Item-Catalog/ItemCatalog/static
			<Directory /var/www/Build-an-Item-Catalog/ItemCatalog/static/>
				Order allow,deny
				Allow from all
			</Directory>
			ErrorLog ${APACHE_LOG_DIR}/error.log
			LogLevel warn
			CustomLog ${APACHE_LOG_DIR}/access.log combined
		</VirtualHost>
2. Enable the server config

		cd /etc/apache2/sites-available/
		sudo a2ensite Build-an-Item-Catalog.conf
3. Create a wsgi file `sudo vim /var/www/Build-an-Item-Catalog/catalog.wsgi`

		#!/usr/bin/python
		import sys
		import logging
		logging.basicConfig(stream=sys.stderr)
		sys.path.insert(0,"/var/www/Build-an-Item-Catalog")

		from ItemCatalog import app as application
		application.secret_key = 'Add your secret key'
4. Restart the server `sudo service apache2 restart`


## References
https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
https://github.com/kongling893/Linux-Server-Configuration-UDACITY

