from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

admin.site.empty_value_display = 'Не задано'


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = (
        'id', 'short_title', 'author', 'cooking_time', 'created',
        'favorites_count'
    )
    list_display_links = ('short_title',)
    list_filter = ('tags', 'author')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('favorites_count',)

    def short_title(self, recipe):
        return recipe.name[:50]
    short_title.short_description = 'Название'

    def favorites_count(self, recipe):
        return recipe.favorited_by.count()
    favorites_count.short_description = 'В избранном'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    list_display_links = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
