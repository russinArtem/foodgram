from django.contrib.auth import get_user_model, update_session_auth_hash
from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.serializers import (
    Base64ImageField,
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscription

User = get_user_model()


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def manage_avatar(self, request):
        profile = request.user.profile
        if request.method == 'PUT':
            image_field = Base64ImageField()
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                validated_avatar = image_field.to_internal_value(avatar_data)
                profile.avatar = validated_avatar
                profile.save()
                return Response(
                    {'avatar': request.build_absolute_uri(profile.avatar.url)},
                    status=status.HTTP_200_OK
                )
            except serializers.ValidationError as validation_error:
                return Response(
                    validation_error.detail, status=status.HTTP_400_BAD_REQUEST
                )
            except Exception:
                return Response(
                    {'avatar': ['Не удалось сохранить аватар.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif request.method == 'DELETE':
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('post',),
        url_path='set_password',
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        if not current_password or not new_password:
            return Response(
                {'detail':
                 'Требуются оба поля: current_password и new_password'
                 },
                status=status.HTTP_400_BAD_REQUEST
            )
        if not user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Subscription.objects.create(user=user, author=author)
        serializer = UserWithRecipesSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk=None):
        author = self.get_object()
        user = request.user
        subscription = Subscription.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user).select_related(
            'author')
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            authors = [sub.author for sub in page]
            serializer = UserWithRecipesSerializer(
                authors, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        authors = [sub.author for sub in subscriptions]
        serializer = UserWithRecipesSerializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        query_params = self.request.query_params
        author = query_params.get('author')
        if author:
            queryset = queryset.filter(author__id=author)
        tags = query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if (
            query_params.get('is_favorited') == '1'
            and user.is_authenticated
        ):
            queryset = queryset.filter(favorited_by=user)
        if (
            query_params.get('is_in_shopping_cart') == '1'
            and user.is_authenticated
        ):
            queryset = queryset.filter(in_shopping_cart_by=user)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_short_link']:
            permission_classes = (AllowAny,)
        else:
            permission_classes = (IsAuthenticated,)
        return [permission() for permission in permission_classes]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_recipe_to_relation(self, request, pk, model, error_message):
        recipe = self.get_object()
        user = request.user
        if model.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'detail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_recipe_from_relation(self, request, pk, model, error_message):
        recipe = self.get_object()
        user = request.user
        relation_item = model.objects.filter(user=user, recipe=recipe)
        if not relation_item.exists():
            return Response(
                {'detail': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        relation_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Вы не можете изменять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Вы не можете изменять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Вы не можете удалять чужой рецепт.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_link = request.build_absolute_uri(f'/s/{recipe.id}/')
        return Response({'short-link': short_link})

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self._add_recipe_to_relation(
            request, pk, ShoppingCart, 'Рецепт уже в корзине.'
        )

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk=None):
        return self._remove_recipe_from_relation(
            request, pk, ShoppingCart, 'Рецепта нет в корзине.'
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        shopping_cart_items = ShoppingCart.objects.filter(
            user=user).select_related('recipe')
        ingredients = {}
        for item in shopping_cart_items:
            recipe = item.recipe
            recipe_ingredients = recipe.recipe_ingredients.select_related(
                'ingredient')
            for ri in recipe_ingredients:
                name = ri.ingredient.name
                unit = ri.ingredient.measurement_unit
                amount = ri.amount
                key = f'{name} ({unit})'
                if key in ingredients:
                    ingredients[key] += amount
                else:
                    ingredients[key] = amount
        lines = []
        for key, amount in ingredients.items():
            lines.append(f'{key} — {amount}')
        content = '\n'.join(lines)
        response = Response(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self._add_recipe_to_relation(
            request, pk, Favorite, 'Рецепт уже в избранном.'
        )

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk=None):
        return self._remove_recipe_from_relation(
            request, pk, Favorite, 'Рецепта нет в избранном.'
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
