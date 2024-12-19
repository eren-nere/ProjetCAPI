import os
from django.core.management.base import BaseCommand
from daphne.server import Server
from daphne.endpoints import build_endpoint_description_strings
from planningpoker.asgi import application  # Import the ASGI application

class Command(BaseCommand):
    help = 'Run the ASGI server'

    def handle(self, *args, **options):
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'planningpoker.settings')
        endpoints = build_endpoint_description_strings(host='127.0.0.1', port='8000')
        server = Server(application=application, endpoints=endpoints)  # Pass the callable application
        server.run()