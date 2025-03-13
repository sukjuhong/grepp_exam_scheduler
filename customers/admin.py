from django.contrib import admin
from django.contrib.auth.models import Group

from customers.models import Customer


class CustomerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'is_active', 'is_admin']
    list_filter = ['is_active']

    search_fields = ['company_name']

    fieldsets = [
        ('Company', {'fields': ['company_name']}),
        ('Permissions', {'fields': ['is_active', 'is_admin']}),
    ]

    add_fieldsets = [
        ('Company', {'fields': ['company_name', 'is_active', 'is_admin']}),
    ]


admin.site.register(Customer, CustomerAdmin)
