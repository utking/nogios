
## Nogios

An attempt to create a Nagios-like health-check system

### Prerequisites

* Python3 (with pip, setuptools, wheel)
* MySQL for storing the database, if MySQL engine is used (with mysql-client)
* Docker and docker-compose for running development using Docker
* Dev packages for Python3 and MySQL, for installing MySQL Python modules (python-dev, libmysqlclient-dev)
* NodeJs and NPM for VueJs-based Web interface

### Development

#### Django

```bash
sudo apt install mysql-client python3-pip python3-setuptools python3-dev libmysqlclient-dev
pip3 install wheel
pip3 install -r requirements.txt
cp ./nogios/settings.example.py ./nogios/settings.py    # and adjust what needed to be adjusted
python3 manage.py check                 # to check the application
python3 manage.py migrate               # to apply DB migrations
python3 manage.py loaddata fixtures/*   # to load initial data
python3 manage.py createsuperuser       # to create an admin user
python3 manage.py runserver             # to start a dev server
```

### Commands

```bash
cp ./nogios/settings.example.py ./nogios/settings.py    # and adjust what needed to be adjusted
pip3 install wheel
pip3 install -r requirements.txt
python3 manage.py migrate               # to apply DB migrations
python3 manage.py loaddata fixtures/*   # to load initial data
python3 manage.py crontab add           # to add a cron job for checks
python3 manage.py verify                # to check Nogios config files
python3 manage.py verify --save         # ... to check and load them if there weren no errors
```

### Nogios config files and other options

* **conf.d** is the default location of config files. But it can be adjusted in settings.py (CONFIG_BASE_PATH)
* **DEFAULT_CHECK_INTERVAL** defines the default check_interval (can be overriden in service/host configs) between the checks
* **DEFAULT_NOTIFICATION_INTERVAL** defines  the default notification_interval (can be overriden) between notifications about service failures
* **DEFAULT_CHECK_CHANNEL** defines the default check channel (can be overriden for any service)
* **CHECK_NRPE_PATH** is the location of check_nrpe binary, if CheckNrpe is configured for services
* **NRPE_PACKET_VERSION** default NRPE protocol verion, if Nrpe channel is configured
* **USE_NOTIFICATIONS_QUEUE** re-routes notifications to a RabbitMQ instance/cluster to be processed by some external workers (not included in the code)
* **NOTIFICATIONS_QUEUE_x** parameters are used to configure RabbitMQ connection properties
* **EMAIL_x** options are used to configure an SMTP server for Email notifications
* **JIRA_x** options are used to configure a Jira connection for notifications creating Jira tickets
* **SSH_x** options define user, private key location, and the key passphrase for Ssh channel (global for all Ssh connections)
* **BASE_URL** defines the base Url for internal use
* **CACHES** defines the global cache backend (local memory, by default)
* **DATABASES** defines the global SQL backend
* **CORS_ORIGIN_WHITELIST** defines CORS for VueJS Web intrface to be able to access Nogios API endpoints

### Important notes

* There is no authentication in the app yet
* **Nrpe channel**: NRPE v3_packet structure is unpacked, which can cause it expecting wrong amount of data. Either use v2_packet or ensure NRPE responds appropriately to v3
* Even though there are separate "Reload [entity]" options, it is recommended to use `verify --save` to reload configuration files, when changed
