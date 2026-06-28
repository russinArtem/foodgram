import json

from django.conf import settings
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
        data_directory = settings.BASE_DIR.parent / 'data'
        if options.get('ingredients'):
            self.import_ingredients(data_directory)
        if options.get('tags'):
            self.import_tags(data_directory)
        if not options.get('ingredients') and not options.get('tags'):
            self.stdout.write(
                self.style.WARNING(
                    'Укажите --ingredients или --tags для импорта.'
                )
            )

    def import_ingredients(self, data_directory):
        file_path = data_directory / 'ingredients.json'
        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден.')
            )
            return
        with open(file_path, 'r', encoding='utf-8') as file:
            ingredients_data = json.load(file)
        created_counter = 0
        for ingredient_item in ingredients_data:
            try:
                ingredient, is_created = Ingredient.objects.get_or_create(
                    name=ingredient_item['name'],
                    measurement_unit=ingredient_item['measurement_unit']
                )
                if is_created:
                    created_counter += 1
            except ValidationError as error:
                self.stdout.write(
                    self.style.ERROR(
                        (
                            f'Ошибка при создании ингредиента '
                            f'{ingredient_item["name"]}: {error}'
                        )
                    )
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'Импортировано {created_counter} ингредиентов.'
            )
        )

    def import_tags(self, data_directory):
        file_path = data_directory / 'tags.json'
        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Файл {file_path} не найден.')
            )
            return
        with open(file_path, 'r', encoding='utf-8') as file:
            tags_data = json.load(file)
        created_counter = 0
        for tag_item in tags_data:
            try:
                tag, is_created = Tag.objects.get_or_create(
                    name=tag_item['name'],
                    slug=tag_item['slug']
                )
                if is_created:
                    created_counter += 1
            except ValidationError as error:
                self.stdout.write(
                    self.style.ERROR(
                        (
                            f'Ошибка при создании тега '
                            f'{tag_item["name"]}: {error}'
                        )
                    )
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'Импортировано {created_counter} тегов.'
            )
        )
