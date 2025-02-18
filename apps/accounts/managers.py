from django.contrib.auth.base_user import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)
    


class ProfileManager(models.Manager):
    def create_profile(self, user, profile_data):
        """Create a profile for the user"""
        return self.create(
            user=user,
            dp=profile_data.get('dp'),
            present_address=profile_data.get('present_address'),
            permanent_address=profile_data.get('permanent_address'),
            nid=profile_data.get('nid'),
            nid_front=profile_data.get('nid_front'),
            nid_back=profile_data.get('nid_back'),
            driving_license=profile_data.get('driving_license'),
            driving_license_front=profile_data.get('driving_license_front'),
            driving_license_back=profile_data.get('driving_license_back'),
          
        )

    def update_profile(self, profile, profile_data):
        """Update an existing profile"""
        profile.dp = profile_data.get('dp', profile.dp)
        profile.present_address = profile_data.get('present_address', profile.present_address)
        profile.permanent_address = profile_data.get('permanent_address', profile.permanent_address)
        profile.nid = profile_data.get('nid', profile.nid)
        profile.nid_front = profile_data.get('nid_front', profile.nid_front)
        profile.nid_back = profile_data.get('nid_back', profile.nid_back)
        profile.driving_license = profile_data.get('driving_license', profile.driving_license)
        profile.driving_license_front = profile_data.get('driving_license_front', profile.driving_license_front)
        profile.driving_license_back = profile_data.get('driving_license_back', profile.driving_license_back)
        profile.save()
        return profile