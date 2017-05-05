# What is it
A simple RESTful web catalog app using the Python framework Flask along which
uses third-party (Google) OAuth authentication.

**Built With** :
* [Flask](http://flask.pocoo.org/) - The web framework used.
* [Jinja2](http://jinja.pocoo.org/docs/2.9/) - The templating engine used.
* [Sqlite3](https://www.sqlite.org/download.html) - The database used.
* [Bootstrap](https://getbootstrap.com/) - The CSS framework used.
* [Python2.7](https://www.python.org/downloads/release/python-2712/) - The server side scripting language used.
* [Glyphicon](http://glyphicons.com/) - The icon pack used.
* [Vagrant](https://www.vagrantup.com/) - Development enviroment.
* [VirtualBox](https://www.virtualbox.org/) - Desktop virtualization sotware.


## Installation
1. Install [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/)
2. Clone my fork of the [fullstack-nanodegree-vm](https://github.com/alklyn/fullstack-nanodegree-vm)
3. Launch the Vagrant VM `vagrant up`
5. Write your Flask application locally in the `vagrant/catalog` directory
   (which will automatically be synced to `/vagrant/catalog` within the VM).
6. Run your application within the VM
`python /vagrant/catalog/final_project.py`
7. Access and test your application by visiting http://localhost:8080 locally
