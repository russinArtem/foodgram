from datetime import datetime

from django.db.models import Sum
from django.template.loader import render_to_string

from recipes.models import RecipeIngredient


def generate_shopping_list(shopping_cart_items):
    recipe_ids = [item.recipe_id for item in shopping_cart_items]
    ingredients_data = (
        RecipeIngredient.objects
        .filter(recipe_id__in=recipe_ids)
        .select_related('ingredient')
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes_info = [
        {
            'name': item.recipe.name,
            'author': item.recipe.author.username,
            'tags': [tag.name for tag in item.recipe.tags.all()],
        }
        for item in shopping_cart_items
    ]
    context = {
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'ingredients': [
            {
                'index': idx + 1,
                'name': item['ingredient__name'].capitalize(),
                'unit': item['ingredient__measurement_unit'],
                'amount': item['total_amount'],
            }
            for idx, item in enumerate(ingredients_data)
        ],
        'recipes': recipes_info,
    }
    return render_to_string('shopping_list.txt', context)
