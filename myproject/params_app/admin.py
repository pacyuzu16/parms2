from django.contrib import admin
from .models import (
    ContactMessage, ParkingLot, Vehicle, ParkingSpace,
    ParkingTicket, Payment, ParkingDetectionEvent, UserNotification
)


class ParkingSpaceInline(admin.TabularInline):
    model = ParkingSpace
    extra = 1


@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('lot_id', 'location', 'total_spaces', 'available_spaces', 'hourly_rate', 'is_active')
    search_fields = ('location',)
    list_filter = ('is_active',)
    inlines = [ParkingSpaceInline]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('vehicle_id', 'plate_number', 'vehicle_type', 'owner_name')
    search_fields = ('plate_number', 'owner_name')
    list_filter = ('vehicle_type',)


@admin.register(ParkingSpace)
class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('space_id', 'space_type', 'is_occupied', 'parking_lot')
    list_filter = ('space_type', 'is_occupied')


@admin.register(ParkingTicket)
class ParkingTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'vehicle', 'parking_space', 'entry_time', 'exit_time', 'fee')
    list_filter = ('entry_time', 'exit_time')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'amount', 'payment_method', 'date', 'ticket')
    readonly_fields = ('date',)
    list_filter = ('payment_method',)


@admin.register(ParkingDetectionEvent)
class ParkingDetectionEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'lot', 'event_type', 'plate_number', 'source', 'confidence', 'detected_at', 'processed')
    list_filter = ('event_type', 'source', 'processed')
    readonly_fields = ('detected_at',)


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notif_type', 'is_read', 'created_at')
    list_filter = ('notif_type', 'is_read')
    readonly_fields = ('created_at',)


admin.site.register(ContactMessage)
