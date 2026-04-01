from django.core.management.base import BaseCommand

from api_clients.models import ApiClient


class Command(BaseCommand):
    help = "Cree un client API M2M et affiche son jeton Bearer une seule fois."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Nom lisible du client API.")
        parser.add_argument(
            "--scope",
            action="append",
            dest="scopes",
            default=[],
            help="Scope a associer au client. Peut etre repete.",
        )
        parser.add_argument(
            "--description",
            default="",
            help="Description libre du client.",
        )

    def handle(self, *args, **options):
        client = ApiClient.objects.create(
            name=options["name"],
            description=options["description"],
            scopes=options["scopes"],
        )
        token = client.rotate_secret()

        self.stdout.write(self.style.SUCCESS("Client API cree avec succes."))
        self.stdout.write(f"client_id: {client.client_id}")
        self.stdout.write(f"scopes: {', '.join(client.scopes) if client.scopes else '-'}")
        self.stdout.write("")
        self.stdout.write("Jeton Bearer a conserver des maintenant :")
        self.stdout.write(token)
