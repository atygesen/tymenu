# TyMenu

The Tygesen Menu system, built in flask.


## Development

Development is done in a Docker container. To start a new container, simply:

```sh
sudo docker-compose up --build
```
and then connect to
```
localhost:8000
```

This creates two containers:

* tymenu
* tymenu_mysql

The first being the Flask app, the second being the MySQL database.
For information on importing an existing SQL database, see the
[backups readme](backups/README.md).
