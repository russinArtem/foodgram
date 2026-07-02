from datetime import datetime

from django.db.models import Sum
from django.template.loader import render_to_string

from .models import RecipeIngredient


def generate_shopping_list(
    shopping_cart_items,
    template_name='shopping_list.txt'
):
    recipe_ids = [item.recipe_id for item in shopping_cart_items]
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe_id__in=recipe_ids)
        .select_related('ingredient')
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    return render_to_string(
        template_name,
        {
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'ingredients': ingredients,
            'recipes': shopping_cart_items,
        }
    )
