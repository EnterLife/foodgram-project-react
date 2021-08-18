from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import (Favorite, Follow, Ingredient, IngredientForRecipe,
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
    queryset = User.objects.all()
    user = serializers.IntegerField(source='user.id')
    author = serializers.IntegerField(source='author.id')

    class Meta:
        model = Follow
        fields = ['user', 'author']

    def validate(self, validated_data):
        user = self.context.get('request').user
        author_id = validated_data['author'].id
        follow_exist = Follow.objects.filter(
            user=user,
            author__id=author_id
        ).exists()

        if self.context.get('request').method == 'GET':
            if user.id == author_id or follow_exist:
                raise serializers.ValidationError(
                    'Вы уже подписаны')
        return validated_data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return ShowFollowsSerializer(
            instance.author,
            context=context).validated_data


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Favorite
        fields = ['user', 'recipe']

    def validate(self, validated_data):
        user = self.context.get('request').user
        recipe_id = validated_data['recipe'].id

        if (self.context.get('request').method == 'GET'
                and Favorite.objects.filter(user=user,
                                            recipe__id=recipe_id).exists()):
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное')

        recipe = get_object_or_404(Recipe, id=recipe_id)

        if (self.context.get('request').method == 'DELETE'
                and not Favorite.objects.filter(
                    user=user,
                    recipe=recipe).exists()):
            raise serializers.ValidationError()

        return validated_data


class PurchaseSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = Purchase
        fields = '__all__'

    def validate(self, validated_data):
        author = self.context.get('request').user
        recipe = validated_data['recipe']
        recipe_exists = Purchase.objects.filter(
            author=author,
            recipe=recipe
        ).exists()
        if recipe_exists:
            raise serializers.ValidationError(
                'Вы уже добавили рецепт в корзину'
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
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Purchase.objects.filter(user=request.user, recipe=obj).exists()

    def validate(self, validated_data):
        ingredients = self.initial_data.get('ingredients')
        for ingredient_item in ingredients:
            if int(ingredient_item['amount']) < 0:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что это значение больше 0.')
                })
        validated_data['ingredients'] = ingredients
        return validated_data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.save()
        recipe.tags.set(tags)
        ingredients_instance = []
        for ingredient in ingredients:
            ingredient_id = Ingredient.objects.get(id=ingredient['id'])
            amount = ingredient['amount']
            ingredients_instance.append(
                IngredientForRecipe(
                    ingredient=ingredient_id,
                    recipe=recipe, amount=amount
                )
            )
        IngredientForRecipe.objects.bulk_create(ingredients_instance)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        IngredientForRecipe.objects.filter(recipe=instance).delete()
        ingredients_instance = []
        for item in ingredients_data:
            amount = item['amount']
            ingredient_id = Ingredient.objects.get(id=item['id'])
            ingredients_instance.append(
                IngredientForRecipe(
                    ingredient=ingredient_id, recipe=instance, amount=amount
                )
            )
        IngredientForRecipe.objects.bulk_create(ingredients_instance)
        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')
        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')
        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        instance.tags.set(tags_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }
        ).data


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
        fields = ['id', 'name', 'image', 'cooking_time']


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
