from django.contrib import admin

from .models import CustomUser, Follow


class UserAdmin(admin.ModelAdmin):
    list_filter = ('username', 'email')


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Follow)
