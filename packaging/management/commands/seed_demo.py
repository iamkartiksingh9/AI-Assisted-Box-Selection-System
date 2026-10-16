from django.core.management.base import BaseCommand

from packaging.models import Box, Product


class Command(BaseCommand):
    help = "Add a small, repeatable catalog of demo products and shipping boxes."

    def handle(self, *args, **options):
        products = [
            {"name": "Ceramic Mug", "length": "8", "width": "8", "height": "10", "weight": "0.35"},
            {"name": "Hardcover Notebook", "length": "21", "width": "14", "height": "2", "weight": "0.55"},
            {"name": "Folded T-Shirt", "length": "25", "width": "20", "height": "4", "weight": "0.30"},
        ]
        boxes = [
            {"name": "Small Mailer", "internal_length": "22", "internal_width": "16", "internal_height": "12", "max_weight": "2", "cost": "1.25"},
            {"name": "Medium Carton", "internal_length": "30", "internal_width": "25", "internal_height": "15", "max_weight": "5", "cost": "2.10"},
            {"name": "Large Carton", "internal_length": "40", "internal_width": "30", "internal_height": "20", "max_weight": "10", "cost": "3.50"},
        ]
        for fields in products:
            Product.objects.update_or_create(name=fields["name"], defaults=fields)
        for fields in boxes:
            Box.objects.update_or_create(name=fields["name"], defaults=fields)
        self.stdout.write(self.style.SUCCESS("Demo catalog ready: 3 products and 3 boxes."))
