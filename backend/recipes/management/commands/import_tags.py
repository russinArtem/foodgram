from .base_import import BaseImportCommand
from recipes.models import Tag


class Command(BaseImportCommand):
    model = Tag
    file_name = 'tags.json'
