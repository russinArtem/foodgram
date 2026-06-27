import json
import os

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = "Импорт ингредиентов и тегов из JSON-файлов"

    def add_arguments(self, parser):
        parser.add_argument(
            '--ingredients',
            action='store_true',
            help='Импортировать ингредиенты из data/ingredients.json'
        )
        parser.add_argument(
            '--tags',
            action='store_true',
            help='Импортировать теги из data/tags.json'
        )

    def handle(self, *args, **options):
        base_dir = os.path.join(os.getcwd(), '..', 'data')

        if options.get('ingredients'):
            self.import_ingredients(base_dir)

        if options.get('tags'):
            self.import_tags(base_dir)

        if not options.get('ingredients') and not options.get('tags'):
            self.stdout.write(
                self.style.WARNING(
                    'Укажите --ingredients или --tags для импорта.'
                )
            )

    def import_ingredients(self, base_dir):
        file_path = os.path.join(base_dir, 'ingredients.json')
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден.')
            )
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        for item in data:
            try:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                if created:
                    created_count += 1
            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка при создании ингредиента {item["name"]}: {e}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Импортировано {created_count} ингредиентов.'
            )
        )

    def import_tags(self, base_dir):
        file_path = os.path.join(base_dir, 'tags.json')
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден.')
            )
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        created_count = 0
        for item in data:
            try:
                tag, created = Tag.objects.get_or_create(
                    name=item['name'],
                    slug=item['slug']
                )
                if created:
                    created_count += 1
            except ValidationError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка при создании тега {item["name"]}: {e}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Импортировано {created_count} тегов.'
            )
        )
