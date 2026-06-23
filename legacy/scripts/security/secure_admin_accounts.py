import argparse
import os
from django.contrib.auth.models import User

# A list of username : password-env-variable tuples for all the users whose password needs to be secured
SECURE_PASSWORDS = [
    ('root', 'OPENSHIKSHA_SUPERUSER_PASSWORD'),
    ('openshiksha_admin_school_1', 'OPENSHIKSHA_SCHOOL_ADMIN_PASSWORD'),
]

def run(*args):
    parser = argparse.ArgumentParser(description="Set secure passwords for standard Admin accounts")

    for username, password_env_var in SECURE_PASSWORDS:
        secure_password = os.getenv(password_env_var)
        # check secure passwords are available via env vars
        assert secure_password is not None

        # change user password
        user = User.objects.get(username=username)
        user.set_password(secure_password)
        user.save()