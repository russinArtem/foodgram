from django.urls import path

from recipes.views import RecipeShortLinkRedirectView

app_name = 'recipes'

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        RecipeShortLinkRedirectView.as_view(),
        name='recipe_short_link'
    ),
]
