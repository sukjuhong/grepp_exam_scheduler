from django.contrib import admin

from reservations.models import Reservation


class ReservationAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time',
                    'end_time', 'customer', 'status']
    list_filter = ('customer', 'date', 'status')
    search_fields = ('customer', 'date', 'status')
    ordering = ('-date', 'start_time')


admin.site.register(Reservation, ReservationAdmin)
