from django.urls import include, path
from rest_framework.routers import DefaultRouter
from users.views import FollowViewSet

from .views import (DownloadShoppingCart, FavouriteViewSet, IngredientViewSet,
                    RecipesViewSet, ShoppingListViewSet, TagsViewSet)

router = DefaultRouter()
router.register('tags', TagsViewSet, basename='tags')
router.register('recipes', RecipesViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users', FollowViewSet, basename='users')

urlpatterns = [
    path('recipes/<int:recipe_id>/favorite/',
         FavouriteViewSet.as_view(), name='add_recipe_to_favorite'),
    path('recipes/<int:recipe_id>/shopping_cart/',
         ShoppingListViewSet.as_view(), name='add_recipe_to_shopping_cart'),
    path('recipes/download_shopping_cart/',
         DownloadShoppingCart.as_view(), name='dowload_shopping_cart'),
    path('', include(router.urls)),
]
