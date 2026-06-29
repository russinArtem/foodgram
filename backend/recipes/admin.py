from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import models
from django.utils.html import mark_safe

from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Subscription,
    Tag,
    User,
)

admin.site.empty_value_display = 'Не задано'


class RecipesCountMixin:
    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        total = queryset.count()
        if total == 0:
            return (
                ('fast', 'Быстрые (0)'),
                ('medium', 'Средние (0)'),
                ('long', 'Долгие (0)'),
            )
        min_time = queryset.aggregate(min=models.Min('cooking_time'))['min']
        max_time = queryset.aggregate(max=models.Max('cooking_time'))['max']
        if min_time is None or max_time is None:
            return (
                ('fast', 'Быстрые (0)'),
                ('medium', 'Средние (0)'),
                ('long', 'Долгие (0)'),
            )
        diff = max_time - min_time
        low_threshold = min_time + diff // 3
        high_threshold = min_time + diff * 2 // 3
        fast_count = queryset.filter(cooking_time__lt=low_threshold).count()
        medium_count = queryset.filter(
            cooking_time__gte=low_threshold,
            cooking_time__lte=high_threshold
        ).count()
        long_count = queryset.filter(cooking_time__gt=high_threshold).count()
        return (
            ('fast', f'Быстрые (до {low_threshold} мин) ({fast_count})'),
            ('medium', (
                f'Средние ({low_threshold}-{high_threshold} мин) '
                f'({medium_count})'
            )),
            ('long', f'Долгие (более {high_threshold} мин) ({long_count})'),
        )

    def queryset(self, request, queryset):
        total = queryset.count()
        if total == 0:
            return queryset
        min_time = queryset.aggregate(min=models.Min('cooking_time'))['min']
        max_time = queryset.aggregate(max=models.Max('cooking_time'))['max']
        if min_time is None or max_time is None:
            return queryset
        diff = max_time - min_time
        low_threshold = min_time + diff // 3
        high_threshold = min_time + diff * 2 // 3
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lt=low_threshold)
        if self.value() == 'medium':
            return queryset.filter(
                cooking_time__gte=low_threshold,
                cooking_time__lte=high_threshold
            )
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=high_threshold)
        return queryset


class IngredientInUseFilter(admin.SimpleListFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_use'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Да'),
            ('no', 'Нет'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(recipes__isnull=True)
        return queryset


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
        'created',
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
        ingredients = recipe.ingredients.all()
        if ingredients:
            return ', '.join([ing.name for ing in ingredients])
        return '—'

    @admin.display(description='Теги')
    @mark_safe
    def tags_display(self, recipe):
        tags = recipe.tags.all()
        if tags:
            return ', '.join([tag.name for tag in tags])
        return '—'

    @admin.display(description='Картинка')
    @mark_safe
    def image_preview(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'width="50" height="50" style="object-fit: cover;" />'
            )
        return '—'


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    list_display_links = ('name',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        'recipes_count',
        'has_recipes'
    )
    list_display_links = ('name',)
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', IngredientInUseFilter)

    @admin.display(description='В рецептах', boolean=True)
    def has_recipes(self, ingredient):
        return ingredient.recipes.exists()


@admin.register(User)
class UserAdmin(RecipesCountMixin, BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count',
        'is_active',
    )
    list_display_links = ('username',)
    list_filter = (
        'is_active',
        'is_staff',
        ('recipes', admin.EmptyFieldListFilter),
        ('subscriptions', admin.EmptyFieldListFilter),
        ('subscribers', admin.EmptyFieldListFilter),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = (
        'avatar_preview',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count',
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'avatar_preview',
                'recipes_count',
                'subscriptions_count',
                'subscribers_count',
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
        return 'Нет аватара'

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.last_name} {user.first_name}'.strip()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
