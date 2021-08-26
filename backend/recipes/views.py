from django.contrib.auth import get_user_model
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.serializers import RecipeSubscriptionSerializer

from .filters import IngredientNameFilter, RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .permissions import AdminOrAuthorOrReadOnly
from .serializers import (IngredientSerializer, PurchaseSerializer,
                          RecipeReadSerializer, RecipeSerializer,
                          TagSerializer)

User = get_user_model()


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny,)
    pagination_class = None
    filterset_class = IngredientNameFilter


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_class = RecipeFilter
    permission_classes = (AdminOrAuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(
        detail=True,
        methods=['GET', 'DELETE'],
        url_path='favorites',
        url_name='favorites',
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'GET':
            obj, created = Favorite.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                return Response(
                    'Рецепт уже в избранном',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeSubscriptionSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        to_delete = get_object_or_404(Favorite, user=user, recipe=recipe)
        to_delete.delete()
        return Response(
            'Удалено из избранного',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['GET', 'DELETE'],
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if self.request.method == 'GET':
            obj, created = ShoppingCart.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                return Response(
                    'Рецепт уже в списке покупок',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeSubscriptionSerializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        to_delete = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        to_delete.delete()
        return Response(
            'Удалено из списка покупок',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=False,
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        user = request.user
        user_shopping_cart = user.shopping_cart.all()
        shopping_cart = ShoppingCart.get_shopping_cart(user_shopping_cart)
        downloadable_shopping_cart = []
        position = 1
        for ingredient, unit in shopping_cart.items():
            downloadable_shopping_cart.append(
                f"{position}. {ingredient} --- {unit['amount']} "
                f"({unit['measurement_unit']})\n"
            )
            position += 1
        filename = 'Shopping_Cart.txt'
        response = HttpResponse(
            downloadable_shopping_cart,
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format(filename)
        )
        return response


class ShoppingCartView(APIView):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'delete']

    def get(self, request, recipe_id):
        user = request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        serializer = PurchaseSerializer(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(recipe=recipe, user=request.user)
        serializer = RecipeSubscriptionSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, recipe_id):
        user = request.user
        cart = get_object_or_404(ShoppingCart, user=user, recipe__id=recipe_id)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
