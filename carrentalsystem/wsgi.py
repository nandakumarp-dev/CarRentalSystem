import os
import sys

# Add your project directory to the Python path
path = '/home/nandhu/CARRENTALPROJECT'
if path not in sys.path:
    sys.path.insert(0, path)

# Add the virtual environment's site-packages to path
venv_site_packages = '/home/nandhu/CARRENTALPROJECT/env/lib/python3.10/site-packages'
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'carrentalsystem.settings'

# Import and run Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()