# What is it
A simple RESTful web catalog app using the Python framework Flask along which
uses third-party (Google) OAuth authentication.

**Built With** :
* [flask](http://flask.pocoo.org/) - The web framework used.
* [jinja2](http://jinja.pocoo.org/docs/2.9/) - The templating engine used.
* [postgres9.5.7](https://www.postgresql.org/docs/9.5/static/index.html) - The database used.
* [python3.6](https://docs.python.org/3.6/) - The server side scripting language used.
* [glyphicon](http://glyphicons.com/) - The icon pack used.
* [bootstrap3](https://getbootstrap.com/) - The CSS framework used.
* [SQLAlchemy](https://www.sqlalchemy.org/) - The ORM used.
* [nginx1.10.0](https://www.nginx.com/) - The webserver used


## Installation
1. Install server os (In my case ubuntu 16.04).
2. Change the port used for ssh [SSH](https://www.ssh.com/ssh/sshd_config/).
3. Configure the Uncomplicated Firewall [(UFW)](https://help.ubuntu.com/community/UFW)
   to only allow incoming connections for SSH (the port you set in step 2),
   HTTP (port 80), and NTP (port 123).
4. Setup key based login & disable password login for ssh.
5. Install and configure Apache to serve a Python mod_wsgi application.
6. Install and configure PostgreSQL.
7. Create a new database user named catalog that has limited permissions to the
   catalog application database.
8. Install flask/sqlalchemy
9. Install git if it not installed
10. Clone the catalog app [catalog](https://github.com/alklyn/catalog)
11. Install nginx 

## [item catalog app](http://192.241.183.134)

