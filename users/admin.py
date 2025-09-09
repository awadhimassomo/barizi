from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'role', 'is_superuser', 'is_staff')
    list_filter = ('role', 'is_superuser', 'is_staff')
    ordering = ('email',)  # ✅ Order by email, not username

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role', {'fields': ('role',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # ✅ Hide 'admin' role for non-superusers
        if not request.user.is_superuser:
            role_choices = [(k, v) for k, v in form.base_fields['role'].choices if k != 'admin']
            form.base_fields['role'].choices = role_choices
        return form

admin.site.register(CustomUser, CustomUserAdmin)
