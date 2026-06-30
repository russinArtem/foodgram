from django.urls import path

from .views import recipe_short_link_redirect

app_name = 'recipes'

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        recipe_short_link_redirect,
        name='recipe_short_link'
    ),
]
