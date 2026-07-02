from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import mark_safe

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)

admin.site.empty_value_display = 'Не задано'


class RecipesCountMixin:
    list_display = ['recipes_count']

    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    RANGES = {
        'fast': {'label': 'Быстрые', 'range': ()},
        'medium': {'label': 'Средние', 'range': ()},
        'long': {'label': 'Долгие', 'range': ()},
    }

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        distinct_times = recipes.values_list(
            'cooking_time', flat=True
        ).distinct()
        if distinct_times.count() < 3:
            return ()
        times_list = sorted(distinct_times)
        n = len(times_list)
        threshold1 = times_list[n // 3]
        threshold2 = times_list[2 * n // 3]
        self.RANGES['fast']['range'] = (times_list[0], threshold1)
        self.RANGES['medium']['range'] = (threshold1 + 1, threshold2)
        self.RANGES['long']['range'] = (threshold2 + 1, times_list[-1])
        fast_count = recipes.filter(
            cooking_time__range=self.RANGES['fast']['range']
        ).count()
        medium_count = recipes.filter(
            cooking_time__range=self.RANGES['medium']['range']
        ).count()
        long_count = recipes.filter(
            cooking_time__range=self.RANGES['long']['range']
        ).count()

        return (
            (
                'fast',
                f'{self.RANGES["fast"]["label"]} '
                f'(до {threshold1} мин) ({fast_count})'
            ),
            (
                'medium',
                f'{self.RANGES["medium"]["label"]} '
                f'({threshold1 + 1}-{threshold2} мин) ({medium_count})'
            ),
            (
                'long',
                f'{self.RANGES["long"]["label"]} '
                f'(более {threshold2} мин) ({long_count})'
            ),
        )

    def queryset(self, request, recipes):
        value = self.value()
        if value in self.RANGES:
            return recipes.filter(
                cooking_time__range=self.RANGES[value]['range']
            )
        return recipes


class IngredientInUseFilter(admin.SimpleListFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_use'

    LOOKUP_CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, ingredients):
        if self.value() == 'yes':
            return ingredients.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return ingredients.filter(recipes__isnull=True)
        return ingredients


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
        'id',
        'short_title',
        'author',
        'cooking_time',
        'favorites_count',
        'ingredients_display',
        'tags_display',
        'image_preview',
    )
    list_display_links = ('short_title',)
    list_filter = ('tags', 'author', CookingTimeFilter)
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'tags__name',
        'ingredients__name',
    )
    readonly_fields = (
        'favorites_count',
        'ingredients_display',
        'tags_display',
        'image_preview',
    )

    @admin.display(description='Название')
    def short_title(self, recipe):
        return recipe.name[:50]

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Продукты')
    @mark_safe
    def ingredients_display(self, recipe):
        return '<br>'.join(
            f'{ri.ingredient.name} — {ri.amount} '
            f'{ri.ingredient.measurement_unit}'
            for ri in recipe.recipe_ingredients.select_related(
                'ingredient'
            )
        )

    @admin.display(description='Теги')
    @mark_safe
    def tags_display(self, recipe):
        return mark_safe(
            '<br>'.join(tag.name for tag in recipe.tags.all())
        )

    @admin.display(description='Картинка')
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'width="50" height="50" style="object-fit: cover;" />'
            )
        return ''


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'slug', *RecipesCountMixin.list_display]
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'measurement_unit',
        *RecipesCountMixin.list_display,
    ]
    list_display_links = ('name',)
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', IngredientInUseFilter)


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_display_links = ('user',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(User)
class UserAdmin(RecipesCountMixin, BaseUserAdmin):
    list_display = [
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        *RecipesCountMixin.list_display,
        'subscriptions_count',
        'author_subscriptions_count',
    ]
    list_display_links = ('username',)
    list_filter = (
        'is_active',
        'is_staff',
        ('recipes', admin.EmptyFieldListFilter),
        ('subscriptions', admin.EmptyFieldListFilter),
        ('author_subscriptions', admin.EmptyFieldListFilter),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = (
        'avatar_preview',
        'recipes_count',
        'subscriptions_count',
        'author_subscriptions_count',
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'avatar_preview',
                'recipes_count',
                'subscriptions_count',
                'author_subscriptions_count',
            )
        }),
    )

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_preview(self, user):
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" '
                f'width="50" height="50" style="border-radius: 50%;" />'
            )
        return ''

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.last_name} {user.first_name}'.strip()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def author_subscriptions_count(self, user):
        return user.author_subscriptions.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
