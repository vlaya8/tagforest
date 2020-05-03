# tagforest

## Description

Django website to share and organize ressources by tagging them with tags related to each other with a directed acyclic graph

## Run a local version of the website

- Install Django (installing it in a virtual environnement is a good way to do it, using virtualenvwrapper for instance)
- Install mariadb, and setup a database called "tagforest" with the right configuration according to the databases section in the settings.py file
- Install sass, and compile scss files by executing `sass scss:static/tags` at the root of the project
- Execute `python manage.py runserver`, and go to http://localhost:8000/
