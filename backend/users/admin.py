from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription, User, UserProfile

admin.site.empty_value_display = 'Не задано'


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'профиль'
    verbose_name_plural = 'Профили'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name', 'is_active'
    )
    list_display_links = ('username',)
    list_filter = ('is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    inlines = (UserProfileInline,)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')
    list_display_links = ('user',)
    search_fields = ('user__username', 'user__email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created')
    list_display_links = ('user',)
    search_fields = (
        'user__username', 'user__email',
        'author__username', 'author__email'
    )
    list_filter = ('created',)
