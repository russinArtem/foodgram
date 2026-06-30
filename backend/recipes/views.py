from django.http import Http404
from django.shortcuts import redirect

from .models import Recipe


def recipe_short_link_redirect(request, recipe_id):
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404('Рецепт не найден.')
    return redirect(f'/recipes/{recipe_id}/')
