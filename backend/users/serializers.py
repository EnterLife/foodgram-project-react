from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from recipes.serializers import RecipeSerializer
from rest_framework import serializers

from .models import CustomUser, Follow


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


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class CustomUserCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'password', 'first_name', 'last_name'
        )


class FollowSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = '__all__'
