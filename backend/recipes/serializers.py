from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (Favorites, Follow, Ingredient, IngredientForRecipe,
                     Purchase, Recipe, Tag)

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    author = serializers.IntegerField(source='author.id')

    class Meta:
        model = Follow
        fields = ['user', 'author']

    def create(self, validated_data):
        author = validated_data.get('author')
        author = get_object_or_404(User, pk=author.get('id'))
        user = validated_data.get('user')
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на самого себя'
            )
        if Follow.objects.filter(
                author=author,
                user=user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны'
            )
        return Follow.objects.create(user=user, author=author)


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Favorites
        fields = ['user', 'recipe']

    def create(self, validated_data):
        user = validated_data["user"]
        recipe = validated_data["recipe"]
        obj, created = Favorites.objects.get_or_create(user=user,
                                                       recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                {
                    "message": "Нельзя добавить повторно в избранное"
                }
            )
        return validated_data


class PurchaseSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Purchase
        fields = '__all__'

    def create(self, validated_data):
        user = validated_data["user"]
        recipe = validated_data["recipe"]
        obj, created = Purchase.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                {"message": "Вы уже добавили рецепт в корзину"}
            )
        return validated_data


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
        return IngredientForRecipeSerializer(
            IngredientForRecipe.objects.get(ingredient=instance.id)
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

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorites.objects.filter(user=request.user, recipe=obj).exists()

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
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            if amount < 1:
                raise serializers.ValidationError(
                    'Убедитесь, что это значение больше 0.'
                )
            ingredient_instance = get_object_or_404(Ingredient,
                                                    pk=ingredient.get('id'))
            IngredientForRecipe.objects.create(recipe=recipe,
                                               ingredient=ingredient_instance,
                                               amount=amount)
        recipe.save()
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        print(ingredients_data)
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.filter(id=instance.id)
        recipe.update(**validated_data)
        ingredients_instance = [
            ingredient for ingredient in instance.ingredients.all()
        ]
        for item in ingredients_data:
            amount = item['amount']
            ingredient_id = item['id']
            if amount < 1:
                raise serializers.ValidationError(
                    'Убедитесь, что это значение больше 0.'
                )
            if IngredientForRecipe.objects.filter(
                    id=ingredient_id, amount=amount
            ).exists():
                ingredients_instance.remove(
                    IngredientForRecipe.objects.get(id=ingredient_id,
                                                    amount=amount
                                                    ).ingredient)
            else:
                IngredientForRecipe.objects.get_or_create(
                    recipe=instance,
                    ingredient=get_object_or_404(Ingredient, id=ingredient_id),
                    amount=amount
                )
        if validated_data.get('image') is not None:
            instance.image = validated_data.get('image', instance.image)
        instance.ingredients.remove(*ingredients_instance)
        instance.tags.set(tags_data)
        return instance


class RecipeReadSerializer(RecipeSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = IngredientForRecipe.objects.filter(recipe=obj)
        return IngredientForRecipeSerializer(ingredients, many=True).data


class RecipeSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "cooking_time"]


class ShowFollowsSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj)
        return RecipeSubscriptionSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        queryset = Recipe.objects.filter(author=obj)
        return queryset.count()
