Rapid Learning Community
========================

General required packages are:

* Python 2.7
* MySQL server
* MySQL client
* Python development environment (for building Python modules)

The required Python packages are listed in requirements.txt; install with pip.
However, you probably need only to install these three, in this order:

* Django
* beautifulsoup4
* django-ckeditor

For MySQL-python, you may want to use your distribution's Python MySQLdb
package. If you want to install that with pip, you'll need the MySQL
client development libraries on your system, and you may need to upgrade
your "distribute" Python package first as well.

Starting a Development Server:
------------------------------
Quick instructions for a development server, subject to change:

1.  Go to rlc/. This might be a little confusing because the repository is
    also named rlc, so you'll have rlc/rlc in your path.

        cd rlc

2.  Create the site's key with this command:

        python genkey.py

3.  Start the mysql client and create a database. You can use any name that
    you like; the example below uses the name "rlc":

        mysql> CREATE DATABASE rlc
               DEFAULT CHARACTER SET utf8
               DEFAULT COLLATE utf8_general_ci;  

    It's important that you specify the character encoding at the beginning
    like this.

4.  Copy siteconfig.py.dist to siteconfig.py, edit to reflect the DB
    configuration that you just created. The user you choose must have
    read/write access to the database you created above.

    You do not need to configure STATIC_ROOT if you'll be running the dev
    server only.

5.  Go back to the main repository directory.

        cd ..

6.  Create the initial unpopulated database tables with this command:

        python manage.py syncdb  

    During the process, you'll be asked if you'd like to create a superuser.
    Create one for yourself.

7.  Create the initial groups and data:

        ./init_data

8.  Start a development server with:  

        python manage.py runserver

    Django will provide you with a URL where you can access your development
    site.

9.  With your browser, go to that URL. Log in with the superuser that you
    created.

10. In that development site, go to the administrative interface at /admin/,
    and add yourself to the "Editor" group (at least).

11. Go back to the root URL; verify that you can access that index. There
    should be a few documents there.

Note that if the data models are changed during development, and you update
your repository, you won't automatically pick up new tables. You must run
the syncdb command shown above to create them.

However, syncdb does not overwrite existing tables, so if a model changes,
you'll need to manually delete any old tables first. It might be easier just
to create a new database, syncdb, and reload the initial data for development
servers (though it is a bit of a pain to recreate your own user). I'm
working on making this process smoother.

