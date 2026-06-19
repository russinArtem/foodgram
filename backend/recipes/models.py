from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название ингредиента',
        unique=True
    )
    measurement_unit = models.CharField(
        max_length=50,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name[:30]} ({self.measurement_unit})'


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name='Название тега',
        unique=True
    )
    slug = models.SlugField(
        max_length=50,
        verbose_name='Slug тега',
        unique=True
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:30]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=256,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (минуты)'
    )
    favorited_by = models.ManyToManyField(
        User,
        through='Favorite',
        related_name='favorites',
        verbose_name='В избранном у пользователей'
    )
    in_shopping_cart_by = models.ManyToManyField(
        User,
        through='ShoppingCart',
        related_name='shopping_cart_recipes',
        verbose_name='В корзине у пользователей'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created',)

    def __str__(self):
        return self.name[:50]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'состав рецепта'
        verbose_name_plural = 'Составы рецептов'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return (
            f'{self.ingredient.name[:30]} - {self.amount} '
            f'{self.ingredient.measurement_unit}'
        )


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_users'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')
