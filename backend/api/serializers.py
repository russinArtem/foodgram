from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
)

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class IngredientInRecipeWriteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = [*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar']
        read_only_fields = fields

    def get_is_subscribed(self, user):
        current_user = getattr(self.context.get('request'), 'user', None)
        return (
            current_user
            and current_user.is_authenticated
            and Subscription.objects.filter(
                user=current_user, author=user
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
    ingredients = IngredientInRecipeReadSerializer(
        source='recipe_ingredients',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',
        )
        read_only_fields = fields

    def _is_recipe_in_relation(self, recipe, model):
        user = getattr(self.context.get('request'), 'user', None)
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
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True
    )
    ingredients = IngredientInRecipeWriteSerializer(
        many=True,
        write_only=True,
        required=True
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'cooking_time',
            'tags', 'ingredients',
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Это поле обязательно.')
        return value

    def _validate_no_duplicates(self, ids, model, field_name, entity_name):
        if len(ids) == len(set(ids)):
            return
        duplicates = {item for item in ids if ids.count(item) > 1}
        duplicate_names = model.objects.filter(
            id__in=duplicates
        ).values_list('name', flat=True)
        raise serializers.ValidationError(
            {
                field_name: [
                    f'{entity_name} повторяются: {duplicate_names}.'
                ]
            }
        )

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        if tags is None:
            raise serializers.ValidationError(
                {'tags': ['Обязательное поле.']}
            )
        if ingredients is None:
            raise serializers.ValidationError(
                {'ingredients': ['Обязательное поле.']}
            )
        if not tags:
            raise serializers.ValidationError(
                {'tags': ['Список тегов не может быть пустым.']}
            )
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': ['Список ингредиентов не может быть пустым.']}
            )
        tag_ids = [tag.id for tag in tags]
        self._validate_no_duplicates(
            tag_ids,
            Tag,
            'tags',
            'Теги'
        )
        ingredient_ids = [item['id'].id for item in ingredients]
        self._validate_no_duplicates(
            ingredient_ids,
            Ingredient,
            'ingredients',
            'Ингредиенты'
        )
        return data

    def _save_recipe_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=ingredient_data.get('id').id,
                amount=ingredient_data.get('amount')
            )
            for ingredient_data in ingredients_data
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self._save_recipe_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.tags.set(validated_data.pop('tags'))
        instance.recipe_ingredients.all().delete()
        self._save_recipe_ingredients(
            instance,
            validated_data.pop('ingredients')
        )
        return super().update(instance, validated_data)


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    recipes = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = [*UserSerializer.Meta.fields, 'recipes_count', 'recipes']
        read_only_fields = fields

    def get_recipes(self, user):
        request = self.context.get('request')
        return RecipeShortSerializer(
            user.recipes.all()[:int(request.query_params.get(
                'recipes_limit', 10**10
            ))],
            many=True,
            context={'request': request}
        ).data
