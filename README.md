Rapid Learning Community
========================

Required packages other than db client (install with pip):

Django (1.5.1+), beautifulsoup4, django-ckeditor

django-ckeditor requires the Python development libraries (such as the
python-dev apt package) in order to build its prerequisites.

These requirements will be put into a requirements.txt file soon.


Quick (incomplete) instructions for a dev server, subject to change:

1. Go to rlc/.

2. Copy siteconfig.py.dist to siteconfig.py, edit to reflect your DB
configuration. You need to create the (empty) database for the name you
choose.

3. Run genkey.py.

4. Go back to main directory.

5. Run python manage.py syncdb (creates initial unpopulated DB tables). Create
a superuser for yourself.

6. Run python manage.py runserver. This should start a development server.

You won't have any data. You can use the /admin/ interface to create some.
However, initial fixtures (datasets) are coming soon.

