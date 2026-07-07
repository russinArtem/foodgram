from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
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

admin.site.unregister(Group)
admin.site.empty_value_display = 'Не задано'


class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value and getattr(value, 'url', None):
            output.append(
                f'<img src="{value.url}" width="150" '
                'style="object-fit: cover; margin-bottom: 8px;" />'
            )
        output.append(super().render(name, value, attrs, renderer))
        return mark_safe(''.join(output))


class RecipesCountMixin:
    list_display = ['recipes_count']

    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'Время приготовления'
    parameter_name = 'cooking_time'

    def lookups(self, request, model_admin):
        recipes = model_admin.get_queryset(request)
        distinct_times = recipes.values_list(
            'cooking_time', flat=True
        ).distinct().order_by('cooking_time')
        n = distinct_times.count()
        if n < 3:
            return ()
        threshold1 = distinct_times[n // 3]
        threshold2 = distinct_times[2 * n // 3]
        self.ranges = {
            'fast': (distinct_times[0], threshold1),
            'medium': (threshold1 + 1, threshold2),
            'long': (threshold2 + 1, distinct_times.last()),
        }
        return (
            ('fast', f'Быстрые (до {threshold1} мин)'),
            ('medium', f'Средние ({threshold1 + 1}-{threshold2} мин)'),
            ('long', f'Долгие (более {threshold2} мин)'),
        )

    def queryset(self, request, recipes):
        value = self.value()
        if hasattr(self, 'ranges') and value in self.ranges:
            return recipes.filter(
                cooking_time__range=self.ranges[value]
            )
        return recipes


class BaseYesNoFilter(admin.SimpleListFilter):
    LOOKUP_CHOICES = (
        ('yes', 'Да'),
        ('no', 'Нет'),
    )

    related_name = 'recipes'

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, items):
        lookup = f'{self.related_name}__isnull'
        if self.value() == 'yes':
            return items.filter(**{lookup: False}).distinct()
        if self.value() == 'no':
            return items.filter(**{lookup: True})
        return items


class RecipesFilter(BaseYesNoFilter):
    title = 'Рецепты'
    parameter_name = 'recipes'


class SubscriptionsFilter(BaseYesNoFilter):
    title = 'Подписки'
    parameter_name = 'subscriptions'
    related_name = 'subscriptions'


class AuthorSubscriptionsFilter(BaseYesNoFilter):
    title = 'Подписки автора'
    parameter_name = 'author_subscriptions'
    related_name = 'author_subscriptions'


class IngredientInUseFilter(BaseYesNoFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_use'


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
        'cooking_time_display',
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

    @admin.display(description=mark_safe('Время<br>(мин)'))
    def cooking_time_display(self, recipe):
        return recipe.cooking_time

    def get_form(self, request, recipe=None, **kwargs):
        form = super().get_form(request, recipe, **kwargs)
        form.base_fields['image'].widget = AdminImageWidget()
        return form


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


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('recipe',)
    search_fields = ('recipe__name', 'ingredient__name')


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
        RecipesFilter,
        SubscriptionsFilter,
        AuthorSubscriptionsFilter,
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = (
        'recipes_count',
        'subscriptions_count',
        'author_subscriptions_count',
    )
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': (
                'avatar',
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

    def get_form(self, request, user=None, **kwargs):
        form = super().get_form(request, user, **kwargs)
        form.base_fields['avatar'].widget = AdminImageWidget()
        return form


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    list_display_links = ('user',)
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
