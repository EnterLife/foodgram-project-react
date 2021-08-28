
from recipes.paginators import PageNumberPagination
from recipes.serializers import UserSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CustomUser, Follow


class FollowViewSet(viewsets.GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def subscriptions(self, request):
        user_qs = CustomUser.objects.filter(following__user=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(user_qs, request)
        serializer = UserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['GET', 'DELETE'])
    def subscribe(self, request, **kwargs):
        user = request.user

        if request.method == 'GET':
            author = self.get_object()
            create = Follow.objects.get_or_create(user=user, author=author)
            if not create:
                return Response({
                    'message': 'Вы уже подписаны',
                    'status': f'{status.HTTP_400_BAD_REQUEST}'
                })
            return Response(status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            count, _ = Follow.objects.filter(
                author__pk=kwargs.get('pk'),
                user=user).delete()
            if count == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response({
                'message': 'Удалено',
                'status': f'{status.HTTP_204_NO_CONTENT}'
            })
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
