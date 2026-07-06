from .base_import import BaseImportCommand
from recipes.models import Ingredient


class Command(BaseImportCommand):
    model = Ingredient
    file_name = 'ingredients.json'
