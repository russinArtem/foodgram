import json
from typing import Optional, Type

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models

from recipes.models import Ingredient, Tag


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON-фикстур."""

    model: Optional[Type[models.Model]] = None
    file_name: Optional[str] = None
    fixture_name: Optional[str] = None

    def handle(self, *args, **options):
        try:
            file_path = settings.BASE_DIR / 'data' / self.file_name
            with open(file_path, 'r', encoding='utf-8') as file:
                created_count = self.model.objects.bulk_create(
                    [self.model(**item) for item in json.load(file)],
                    ignore_conflicts=True
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Импортировано {len(created_count)} {self.fixture_name} '
                    f'из файла {self.file_name}.'
                )
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f'Файл {self.file_name} не найден в директории data/'
                )
            )
        except json.JSONDecodeError as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка парсинга JSON в файле {self.file_name}: {error}'
                )
            )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при импорте {self.fixture_name}: {error}'
                )
            )


class CommandImportIngredients(BaseImportCommand):
    """Команда для импорта ингредиентов."""

    model = Ingredient
    file_name = 'ingredients.json'
    fixture_name = 'ингредиентов'


class CommandImportTags(BaseImportCommand):
    """Команда для импорта тегов."""

    model = Tag
    file_name = 'tags.json'
    fixture_name = 'тегов'
