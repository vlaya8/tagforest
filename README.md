# Tagforest website source code

## Description

Repository for [tagforest.fr](https://tagforest.fr), a django website to share and organize knowledge 
and ressources by classifying them with tags. Learn more about the website [here](https://tagforest.fr/about/)

## Run a local version of the website

- Install Django (installing it in a virtual environnement is a good way to do it, using virtualenvwrapper for instance)
- Setup a SQL database accordingly to the configuration in settings.py: the settings.py file is setup to be used with mariadb, but sqllite3 or postgre for instance can be easily used by changing the settings.py settings, see [the documentation](https://docs.djangoproject.com/en/3.0/ref/databases/) for more information
- Clone the git project, make the migrations with `python manage.py migrate`
- Install sass, and compile scss files by executing `sass scss:static/tags` at the root of the project
- Execute `python manage.py compilemessages` to compile the translations in locales/django.po
- Execute `python manage.py runserver`, and go to http://localhost:8000/

## Git workflow

feature git workflow is used:

- Nothing is commited directly to master and dev, and these branches are never rebased
- All other branches are rebased before each merge to ensure a clean history, and to ensure
everything compiles at each commit
- Other branches are either feature branches, hotfix or release, and end up being merged to dev
- Commits are in english and imperative
- Each merge to master is tagged as a new version
