from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.db import models

# Define user roles
USER_ROLES = [
    ('admin', 'Admin'),       # 🔥 Hidden from UI but usable
    ('operator', 'Operator'),
    ('planner', 'Planner'),
    ('vendor', 'Vendor'),
    ('customer', 'Customer'),
]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, role='planner', **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        if not role:
            raise ValueError("The Role field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        # Automatically assign 'admin' role to superusers
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=USER_ROLES, default='planner')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']  # ✅ Include 'role' as a required field

    def __str__(self):
        return self.email
