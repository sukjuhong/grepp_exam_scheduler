from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class CustomerManager(BaseUserManager):
    def create_user(self, company_name: str, password: str = None):
        if not company_name:
            raise ValueError("must have company name")

        user = self.model(
            company_name=company_name
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, company_name: str, password: str = None):
        user = self.create_user(
            company_name=company_name,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class Customer(AbstractBaseUser):
    company_name = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = CustomerManager()

    USERNAME_FIELD = 'company_name'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.company_name

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin
