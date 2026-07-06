import json
from typing import Optional, Type

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models


class BaseImportCommand(BaseCommand):
    model: Optional[Type[models.Model]] = None
    file_name: Optional[str] = None

    def handle(self, *args, **options):
        fixture_name = self.model._meta.verbose_name_plural
        try:
            file_path = settings.BASE_DIR / 'data' / self.file_name
            with open(file_path, 'r', encoding='utf-8') as file:
                created = self.model.objects.bulk_create(
                    (self.model(**item) for item in json.load(file)),
                    ignore_conflicts=True
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Импортировано {len(created)} {fixture_name} '
                    f'из файла {self.file_name}.'
                )
            )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка при импорте {fixture_name}: {error}'
                )
            )
