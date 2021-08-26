from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Follow
from .serializers import ShowFollowsSerializer

User = get_user_model()


class CustomUserViewSet(UserViewSet):

    @action(
        detail=True,
        methods=['GET', 'DELETE'],
        url_path='subscribe',
        url_name='subscribe'
    )
    def subscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, id=pk)
        if user == author:
            return Response(
                'Подписка на самого себя запрещена',
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.request.method == 'GET':
            obj, created = Follow.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                return Response(
                    'Вы уже подписаны на этого пользователя',
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ShowFollowsSerializer(author)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        to_delete = get_object_or_404(Follow, user=user, author=author)
        to_delete.delete()
        return Response(
            'Вы отписались от пользователя',
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False,
            methods=["GET"],
            url_path='subscriptions',
            url_name='subscriptions',
            permission_classes=[permissions.IsAuthenticated])
    def show_follows(self, request):
        user = request.user
        subscription = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscription)
        if page is not None:
            serializer = ShowFollowsSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = ShowFollowsSerializer(
            subscription,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
