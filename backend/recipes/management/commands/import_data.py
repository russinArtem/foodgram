import json
from typing import Optional, Type

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models

from recipes.models import Ingredient, Tag


class BaseImportCommand(BaseCommand):
    model: Optional[Type[models.Model]] = None
    file_name: Optional[str] = None

    def handle(self, *args, **options):
        fixture_name = self.model._meta.verbose_name_plural
        try:
            file_path = settings.BASE_DIR / 'data' / self.file_name
            with open(file_path, 'r', encoding='utf-8') as file:
                objects_created = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Импортировано {len(objects_created)} {fixture_name} '
                    f'из файла {self.file_name}.'
                )
            )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при импорте {fixture_name}: {error}'
                )
            )


class CommandImportIngredients(BaseImportCommand):
    model = Ingredient
    file_name = 'ingredients.json'


class CommandImportTags(BaseImportCommand):
    model = Tag
    file_name = 'tags.json'


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
        if options.get('ingredients'):
            CommandImportIngredients().handle(*args, **options)
        if options.get('tags'):
            CommandImportTags().handle(*args, **options)
        if not options.get('ingredients') and not options.get('tags'):
            self.stdout.write(
                self.style.WARNING(
                    'Укажите --ingredients или --tags для импорта.'
                )
            )
