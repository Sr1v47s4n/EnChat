from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

DEFAULT_PROFILE_PICS = [
    "https://r00tus34.me/EnChat/EnChat/assests/1.png",
    "https://r00tus34.me/EnChat/EnChat/assests/2.png",
    "https://r00tus34.me/EnChat/EnChat/assests/3.png",
    "https://r00tus34.me/EnChat/EnChat/assests/4.png",
    "https://r00tus34.me/EnChat/EnChat/assests/5.png",
    "https://r00tus34.me/EnChat/EnChat/assests/6.png",
]


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, profile_picture=None, is_private=False):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email)
        user.set_password(password)

        # Assign default profile picture if not chosen
        if profile_picture and profile_picture in DEFAULT_PROFILE_PICS:
            user.profile_picture = profile_picture
        else:
            user.profile_picture = DEFAULT_PROFILE_PICS[0]  # Default to first image
        if is_private is not None:
            user.is_private = is_private 
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.create_user(username, email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    profile_picture = models.CharField(
        max_length=100, choices=[(pic, pic) for pic in DEFAULT_PROFILE_PICS]
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)
    slug = models.SlugField(max_length=50)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def slugify():
        import random, string

        slug = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        if User.objects.filter(slug=slug).exists():
            slug = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slugify()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
