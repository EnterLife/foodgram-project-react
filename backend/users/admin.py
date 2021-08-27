from django.contrib import admin

from .models import CustomUser, Follow


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'username')


class FollowAdmin(admin.ModelAdmin):
    list_display = ('author', 'user', 'created_at')
    list_filter = ('created_at',)


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Follow, FollowAdmin)
