import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from djoser.serializers import TokenCreateSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('name', 'measurement_unit')


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source='profile.avatar', required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from users.models import Subscription
            return Subscription.objects.filter(
                user=request.user, author=user
            ).exists()
        return False


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomTokenCreateSerializer(TokenCreateSerializer):
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        if not email or not password:
            raise serializers.ValidationError('Email и пароль обязательны.')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                'Невозможно войти с предоставленными учетными данными.'
            )
        if not user.check_password(password):
            raise serializers.ValidationError(
                'Невозможно войти с предоставленными учетными данными.'
            )
        if not user.is_active:
            raise serializers.ValidationError('Пользователь не активирован.')
        self.user = user
        return attrs


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True, allow_null=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_tags(self, recipe):
        return TagSerializer(recipe.tags.all(), many=True).data

    def get_ingredients(self, recipe):
        recipe_ingredients = recipe.recipe_ingredients.select_related(
            'ingredient'
        )
        return [
            {
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            }
            for ri in recipe_ingredients
        ]

    def _is_recipe_in_relation(self, recipe, model):
        user = self.context.get('request').user
        if user and user.is_authenticated:
            return model.objects.filter(user=user, recipe=recipe).exists()
        return False

    def get_is_favorited(self, recipe):
        return self._is_recipe_in_relation(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self._is_recipe_in_relation(recipe, ShoppingCart)

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
        if len(tags_data) != len(set(tags_data)):
            raise serializers.ValidationError(
                {'tags': ['Теги не должны повторяться.']}
            )
        existing_tags = set(
            Tag.objects.filter(id__in=tags_data).values_list('id', flat=True)
        )
        non_existing_tags = set(tags_data) - existing_tags
        if non_existing_tags:
            raise serializers.ValidationError(
                {'tags': [
                    f'Теги с id {list(non_existing_tags)} не существуют.'
                ]}
            )
        seen_ingredients = set()
        for ing_data in ingredients_data:
            ingredient_id = ing_data.get('id')
            if ingredient_id in seen_ingredients:
                raise serializers.ValidationError(
                    {'ingredients': ['Ингредиенты не должны повторяться.']}
                )
            seen_ingredients.add(ingredient_id)

    def _create_recipe_ingredient(self, recipe, ingredient_data):
        ingredient_id = ingredient_data.get('id')
        amount = ingredient_data.get('amount')
        if not ingredient_id:
            raise serializers.ValidationError(
                {'ingredients': [
                    'Для каждого ингредиента требуется поле id.'
                ]}
            )
        if not amount:
            raise serializers.ValidationError(
                {'ingredients': [
                    'Для каждого ингредиента требуется поле amount.'
                ]}
            )
        try:
            ingredient = Ingredient.objects.get(id=ingredient_id)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                {'ingredients': [
                    f'Ингредиент с id {ingredient_id} не существует.'
                ]}
            )
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=amount
        )

    def create(self, validated_data):
        request = self.context.get('request')
        tags_data = request.data.get('tags')
        ingredients_data = request.data.get('ingredients')
        self._validate_tags_and_ingredients(tags_data, ingredients_data)
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            self._create_recipe_ingredient(recipe, ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        request = self.context.get('request')
        tags_data = request.data.get('tags')
        ingredients_data = request.data.get('ingredients')
        self._validate_tags_and_ingredients(tags_data, ingredients_data)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.tags.set(tags_data)
        instance.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            self._create_recipe_ingredient(instance, ingredient_data)
        return instance


class UserWithRecipesSerializer(UserSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes_count', 'recipes'
        )

    def get_recipes_count(self, user):
        return user.recipes.count()

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


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
