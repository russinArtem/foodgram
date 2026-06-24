from django.contrib.auth import get_user_model
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

MIN_COOKING_TIME = 1

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', required=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = DjoserUserCreateSerializer.Meta.fields + (
            'first_name', 'last_name',
        )


class UserSerializer(DjoserUserSerializer):
    avatar = serializers.ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed', 'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and Subscription.objects.filter(
                user=request.user, author=user
            ).exists()
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )

    def _is_recipe_in_relation(self, recipe, model):
        user = self.context.get('request').user
        return (
            user
            and user.is_authenticated
            and model.objects.filter(user=user, recipe=recipe).exists()
        )

    def get_is_favorited(self, recipe):
        return self._is_recipe_in_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._is_recipe_in_relation(recipe, ShoppingCart)


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags_data = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True
    )
    ingredients_data = serializers.ListField(
        child=IngredientInRecipeSerializer(),
        write_only=True,
        required=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags_data', 'ingredients_data',
        )

    def _validate_no_duplicates(self, ids, model, field_name, error_template):
        if len(ids) != len(set(ids)):
            duplicates = [item for item in ids if ids.count(item) > 1]
            unique_duplicates = list(set(duplicates))
            duplicate_names = model.objects.filter(
                id__in=unique_duplicates
            ).values_list('name', flat=True)
            raise serializers.ValidationError(
                {field_name: [error_template.format(list(duplicate_names))]}
            )

    def _validate_tags_and_ingredients(self, tags_data, ingredients_data):
        if tags_data is None:
            raise serializers.ValidationError({'tags': ['Обязательное поле.']})
        if ingredients_data is None:
            raise serializers.ValidationError(
                {'ingredients': ['Обязательное поле.']}
            )
        if not tags_data:
            raise serializers.ValidationError(
                {'tags': ['Список тегов не может быть пустым.']}
            )
        if not ingredients_data:
            raise serializers.ValidationError(
                {'ingredients': ['Список ингредиентов не может быть пустым.']}
            )
        self._validate_no_duplicates(
            tags_data,
            Tag,
            'tags',
            'Теги {} повторяются.'
        )
        ingredient_ids = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data.get('id')
            ingredient_ids.append(ingredient_id)
        self._validate_no_duplicates(
            ingredient_ids,
            Ingredient,
            'ingredients',
            'Ингредиенты {} повторяются.'
        )

    def _save_recipe_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_data.get('id'),
                    amount=ingredient_data.get('amount')
                )
                for ingredient_data in ingredients_data
            ]
        )

    def create(self, validated_data):
        tags_data = validated_data.pop('tags_data')
        ingredients_data = validated_data.pop('ingredients_data')
        self._validate_tags_and_ingredients(tags_data, ingredients_data)
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._save_recipe_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags_data', None)
        ingredients_data = validated_data.pop('ingredients_data', None)
        self._validate_tags_and_ingredients(tags_data, ingredients_data)
        recipe = super().update(instance, validated_data)
        recipe.tags.set(tags_data)
        recipe.recipe_ingredients.all().delete()
        self._save_recipe_ingredients(recipe, ingredients_data)
        return recipe


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + (
            'recipes_count', 'recipes',
        )
        read_only_fields = fields

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = user.recipes.all()
        if recipes_limit:
            try:
                limit = int(recipes_limit)
                recipes = recipes[:limit]
            except ValueError:
                pass
        return RecipeShortSerializer(
            recipes, many=True, context={'request': request}
        ).data
