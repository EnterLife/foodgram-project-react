from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from users.serializers import CustomUserSerializer
from users.models import Follow
from .models import (Favorite, Ingredient, IngredientForRecipe, Recipe,
                     ShoppingCart, Tag)


class TagSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug')

    def validate_id(self, id_):
        if not Tag.objects.filter(id=id_).exists():
            msg = f'Tag with id `{id_}` does not exist.'
            raise serializers.ValidationError(msg)
        return id_


class PurchaseSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(source='user.id')
    recipe = serializers.IntegerField(source='recipe.id')

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def validate(self, data):
        user = data['user']['id']
        recipe = data['recipe']['id']
        if ShoppingCart.objects.filter(user=user, recipe__id=recipe).exists():
            raise serializers.ValidationError(
                {
                    "errors": "Вы уже добавили рецепт в корзину"
                }
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount',
        ]
        read_only_fields = ['name', 'measurement_unit']

    def validate_id(self, id_):
        if not Ingredient.objects.filter(id=id_).exists():
            msg = f'Ingredient with id `{id_}` does not exist.'
            raise serializers.ValidationError(msg)
        return id_

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError(
                'Количество ингридиента должно быть больше нуля!')
        return amount


class IngredientForRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientForRecipe
        fields = ['id', 'ingredient', 'recipe', 'amount']


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)
    image = Base64ImageField(
        max_length=None,
        required=True,
        allow_empty_file=False,
        use_url=True,
    )
    author = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        ]

    def get_author(self, recipe):
        return UserSerializer(recipe.author, omit=['recipes']).data

    def get_is_favorited(self, recipe):
        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        user = request.user
        return Favorite.objects.filter(recipe=recipe, user=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        user = request.user
        return ShoppingCart.objects.filter(recipe=recipe, user=user).exists()

    def create(self, validated_data):
        tags_data = validated_data.pop('tags')

        ingredients_data = validated_data.pop('ingredients')
        author = self.context.get('request').user

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.save()
        recipe.tags.set(tags_data)

        IngredientForRecipe.objects.bulk_create([
            IngredientForRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']) for ingredient in
            ingredients_data
        ])

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        IngredientForRecipe.objects.filter(recipe=instance).delete()

        IngredientForRecipe.objects.bulk_create([
            IngredientForRecipe(
                recipe=instance,
                ingredient=Ingredient.objects.get(id=ingredient['id']),
                amount=ingredient['amount']) for ingredient in
            ingredients_data
        ])

        instance.name = validated_data.pop('name')
        instance.text = validated_data.pop('text')

        if validated_data.get('image') is not None:
            instance.image = validated_data.pop('image')

        instance.cooking_time = validated_data.pop('cooking_time')
        instance.save()
        instance.tags.set(tags_data)

        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        tags_data = TagSerializer(instance.tags.all(), many=True).data

        ings = instance.ingredientforrecipe_set.prefetch_related('ingredient').all() # noqa
        ingredients_data = [
            {
                **IngredientSerializer(ingredient_in_recipe.ingredient).data,
                'amount': ingredient_in_recipe.amount
            } for ingredient_in_recipe in ings
        ]

        return {**data, 'tags': tags_data, 'ingredients': ingredients_data}


class RecipeReadSerializer(RecipeSerializer):
    tags = TagSerializer(read_only=True, many=True)
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        ingredients = IngredientForRecipe.objects.filter(recipe=obj)
        return IngredientForRecipeSerializer(ingredients, many=True).data


class UserSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'purchases',
            'is_subscribed',
            'recipes',
            'recipes_count',
        ]

    def __init__(self, *args, **kwargs):
        omit = kwargs.pop('omit', [])
        super().__init__(*args, **kwargs)
        for field in omit:
            del self.fields[field]

    def get_is_subscribed(self, user):
        request = self.context.get('request')

        if request is None or request.user.is_anonymous:
            return False

        return Follow.objects.filter(user=request.user, author=user).exists()

    def get_recipes_count(self, user):
        return user.recipes.count()
