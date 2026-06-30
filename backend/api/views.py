from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)
from recipes.services import generate_shopping_list

User = get_user_model()


class DefaultPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'


class UserViewSet(DjoserUserViewSet):
    pagination_class = DefaultPagination

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def manage_avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
                user.avatar = None
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            raise serializers.ValidationError(
                {'avatar': ['Это поле обязательно.']}
            )
        validated_avatar = Base64ImageField().to_internal_value(avatar_data)
        user.avatar = validated_avatar
        user.save()
        return Response(
            {'avatar': request.build_absolute_uri(user.avatar.url)},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription, user=user, author_id=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = self.get_object()
        if user == author:
            raise serializers.ValidationError(
                {'detail': 'Нельзя подписаться на самого себя.'}
            )
        _, created = Subscription.objects.get_or_create(
            user=user, author=author
        )
        if not created:
            raise serializers.ValidationError(
                {'detail': f'Вы уже подписаны на {author.username}.'}
            )
        return Response(
            UserWithRecipesSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                [sub.author for sub in self.paginate_queryset(
                    request.user.subscriptions.select_related('author')
                )],
                many=True,
                context={'request': request}
            ).data
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = DefaultPagination
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _add_recipe_to_relation(self, request, pk, model):
        recipe = self.get_object()
        _, created = model.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            raise serializers.ValidationError(
                {'detail': (
                    f'Рецепт "{recipe.name}" уже добавлен в '
                    f'{model._meta.verbose_name}.'
                )}
            )
        return Response(
            RecipeShortSerializer(
                recipe, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    def _remove_recipe_from_relation(self, request, model, pk=None):
        get_object_or_404(
            model,
            user=request.user,
            recipe_id=pk
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link'
    )
    def get_short_link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)
        return Response(
            {'short-link': request.build_absolute_uri(
                reverse('recipes:recipe_short_link', args=[pk])
            )}
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self._add_recipe_to_relation(
            request, pk, ShoppingCart
        )

    @shopping_cart.mapping.delete
    def delete_from_shopping_cart(self, request, pk=None):
        return self._remove_recipe_from_relation(
            request, ShoppingCart, pk
        )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        return FileResponse(
            generate_shopping_list(
                request.user.shoppingcarts.select_related('recipe')
            ),
            content_type='text/plain',
            as_attachment=True,
            filename='shopping_list.txt'
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self._add_recipe_to_relation(
            request, pk, Favorite
        )

    @favorite.mapping.delete
    def delete_from_favorite(self, request, pk=None):
        return self._remove_recipe_from_relation(
            request, Favorite, pk
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
