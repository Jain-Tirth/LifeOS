#!/usr/bin/env python
"""
Helper script for production operations.
Usage: python manage_prod.py migrate --database=default
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeos.settings_prod')
    django.setup()

    # Print database info for verification
    print(f"Database: {settings.DATABASES['default']['NAME']}")
    print(f"Host: {settings.DATABASES['default']['HOST']}")
    print(f"SSL: {settings.DATABASES['default']['OPTIONS']['sslmode']}")

    execute_from_command_line(sys.argv)
