Flaskr
======

The basic blog app built in the Flask `tutorial`_.

.. _tutorial: https://flask.palletsprojects.com/tutorial/


Install
-------

**Be sure to use the same version of the code as the version of the docs
you're reading.** You probably want the latest tagged version, but the
default Git version is the main branch. ::

    # clone the repository
    $ git clone https://github.com/pallets/flask
    $ cd flask
    # checkout the correct version
    $ git tag  # shows the tagged versions
    $ git checkout latest-tag-found-above
    $ cd examples/tutorial

Create a virtualenv and activate it::

    $ python3 -m venv .venv
    $ . .venv/bin/activate

Or on Windows cmd::

    $ py -3 -m venv .venv
    $ .venv\Scripts\activate.bat

Install Flaskr::

    $ pip install -e .


Setup w/ different runs
---


to run just with flask::

    flask --app flaskr init-db
    flask --app flaskr run --debug


to install gunicorn/nginx::
    
    pip install gunicorn # make sure you are in the pythong venv
    sudo apt install nginx

to start gunicorn::
    gunicorn -w 4 "flaskr:create_app()"

to create the nginx server::
    
    cd /etc/nginx/sites-available
    sudo vim appname

put in::
    
    server {
        listen 80;
        server_name your_domain.com;  # Change to your domain or public IP

        location / {
            proxy_pass http://127.0.0.1:8000;  # Gunicorn is running on port 8000
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

Check there are no syntax errors::

    sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
    sudo nginx -t

Then start it::

    sudo systemctl restart nginx


