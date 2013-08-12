Rapid Learning Community
========================

Quick (incomplete) Instructions for a dev server, subject to change:

1. Go to rlc/.

2. Copy siteconfig.py.dist to siteconfig.py, edit to reflect your DB
configuration. You need to create the (empty) database for the name you
choose.

3. Run genkey.py.

4. Go back to main directory.

5. Run python manage.py syncdb (creates initial unpopulated DB tables). Create
a superuser for yourself.

6. Run python runserver. This should start a development server.

