from django.contrib import admin
from .models import ContactMessage, ParkingLot, Vehicle, ParkingSpace, ParkingTicket, User, Payment

# Parking Space Inline
class ParkingSpaceInline(admin.TabularInline):
    model = ParkingSpace
    extra = 1

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('lot_id', 'location', 'total_spaces', 'available_spaces')
    search_fields = ('location',)
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
    list_editable = ('exit_time', 'fee')
    list_filter = ('entry_time', 'exit_time')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'role', 'contact_info')
    search_fields = ('name', 'contact_info')
    list_filter = ('role',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'amount', 'payment_method', 'date', 'ticket')
    readonly_fields = ('date',)
    list_filter = ('payment_method',)


admin.site.register(ContactMessage)
