from django.shortcuts import get_object_or_404
from django.views.generic import RedirectView

from recipes.models import Recipe


class RecipeShortLinkRedirectView(RedirectView):
    permanent = False

    def get_redirect_url(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['recipe_id'])
        return request.build_absolute_uri(f'/recipes/{recipe.id}/')
