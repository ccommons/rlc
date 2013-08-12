#!/usr/bin/env python

# Use this to generate a secret key in secretkey.py if you need one.
# This uses the Django-supplied method of generating the key.

import os, stat, sys

from django.utils.crypto import get_random_string

KEY_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'

SECRET_FILE="secretkey.py"

try:
    file_info = os.stat(SECRET_FILE)
    sys.stderr.write("error: won't clobber existing secret file " + SECRET_FILE)
    sys.stderr.write("\n")
    # file exists; abort
    exit(1)
except OSError:
    # file doesn't exist; proceed
    pass

fd = open(SECRET_FILE, "w")

fd.write("SECRET_KEY = '")
fd.write(get_random_string(50, KEY_CHARS))
fd.write("'\n")

fd.close()

# change to user-read/write only
os.chmod(SECRET_FILE, stat.S_IWUSR | stat.S_IRUSR)

print("key file " + SECRET_FILE + " generated.")

