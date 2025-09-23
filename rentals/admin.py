from django.contrib import admin
from .models import Brand, VehicleType, Vehicle, Feature, VehicleImage

# Register your models here.

admin.site.register(Brand)
admin.site.register(VehicleType)
admin.site.register(Feature)

class VehicleImageInline(admin.TabularInline):

    model  = VehicleImage

    extra = 3

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):

    inlines = [VehicleImageInline]
    
    list_display = ['name','brand','vehicle_type','daily_rent', 'availability_status']
    
