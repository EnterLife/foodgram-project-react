from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from users.serializers import CustomUserSerializer

from .models import (Favorite, Ingredient, IngredientForRecipe, Purchase,
                     Recipe, Tag)

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def validate(self, data):
        user = data['user']['id']
        recipe = data['recipe']['id']
        if Favorite.objects.filter(user=user, recipe__id=recipe).exists():
            raise serializers.ValidationError(
                {
                    "errors": "Рецепт уже добавлен в избранное"
                }
            )
        return data

    def create(self, validated_data):
        user = validated_data["user"]
        recipe = validated_data["recipe"]
        Favorite.objects.get_or_create(user=user, recipe=recipe)
        return validated_data


class PurchaseSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, data):
        user = data['user']['id']
        recipe = data['recipe']['id']
        if Purchase.objects.filter(user=user, recipe__id=recipe).exists():
            raise serializers.ValidationError(
                {
                    "errors": "Вы уже добавили рецепт в корзину"
                }
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField()
    measurement_unit = serializers.ReadOnlyField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientForRecipeSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientForRecipe
        fields = ['id', 'name', 'amount', 'measurement_unit']


class IngredientForRecipeCreate(IngredientForRecipeSerializer):
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    def to_representation(self, instance):
        recipe = [i for i in instance.recipe_set.all()]
        return IngredientForRecipeSerializer(
            IngredientForRecipe.objects.filter(recipe=recipe[0].id), many=True
        ).data


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    author = CustomUserSerializer(read_only=True)
    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = IngredientForRecipeCreate(many=True)

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time', 'pub_date'
        ]

    def validate(self, data):
        errors_data = {
            'duplicate_recipes': {
                "errors": f"Рецепт с таким названием: {data['name']} уже "
                          f"существует"},
            'duplicate_ingredients': {
                "errors": "Такой ингредиент уже существует"},
            'amount_field': {
                'amount': 'Убедитесь, что указали значение больше 0.'}
        }
        request = self.context['request']
        ingredients = data['ingredients']
        exist_recipe = Recipe.objects.filter(name=data['name']).exists()
        if request.method == 'POST' and exist_recipe:
            raise serializers.ValidationError(errors_data['duplicate_recipes'])
        unique_ingredients = []
        for ingredient in ingredients:
            if ingredient['id'] in unique_ingredients:
                raise serializers.ValidationError(
                    errors_data['duplicate_ingredients']
                )
            elif ingredient['amount'] < 1:
                raise serializers.ValidationError(errors_data['amount_field'])
            unique_ingredients.append(ingredient['id'])
        return data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Purchase.objects.filter(user=request.user, recipe=obj).exists()

    def create(self, validated_data):
        request = self.context.get('request')
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=request.user, **validated_data)
        recipe.tags.set(tags_data)
        ingredient_in_recipe = [IngredientForRecipe(
            recipe=recipe,
            ingredient=get_object_or_404(Ingredient, pk=ingredient['id']),
            amount=ingredient['amount']
        )
            for ingredient in ingredients
        ]
        IngredientForRecipe.objects.bulk_create(ingredient_in_recipe)
        recipe.save()
        return recipe

    def update(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe.ingredients.clear()
        ingredient_in_recipe = [IngredientForRecipe(
            recipe=recipe,
            ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
            amount=ingredient['amount']
        )
            for ingredient in ingredients
        ]
        IngredientForRecipe.objects.bulk_create(ingredient_in_recipe)
        if validated_data.get('image') is not None:
            recipe.image = validated_data.get('image', recipe.image)
        recipe.tags.set(tags_data)
        return super().update(recipe, validated_data)


class RecipeReadSerializer(RecipeSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = IngredientForRecipe.objects.filter(recipe=obj)
        return IngredientForRecipeSerializer(ingredients, many=True).data
