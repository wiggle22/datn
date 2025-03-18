from django.contrib import admin
from django.contrib.auth.models import Group
from .models import ParkingLot, ParkingRecord, Reservation, Customer, Payment_VNPay
from django.urls import path
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta

class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'view_details_link')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(admin=request.user)

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set admin during the creation
            obj.admin = request.user
        super().save_model(request, obj, form, change)

    def view_details_link(self, obj):
        return format_html('<a href="{}">View Details</a>', obj.get_absolute_url())
    view_details_link.short_description = 'Details'
    view_details_link.allow_tags = True

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/details/', self.admin_site.admin_view(self.details_view), name='parkinglot_details'),
        ]
        return custom_urls + urls

    def details_view(self, request, pk):
        parking_lot = get_object_or_404(ParkingLot, pk=pk)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        #customers = Customer.objects.filter(parking_lots=parking_lot)
        records = ParkingRecord.objects.filter(lot=parking_lot)
        entries_today = ParkingRecord.objects.filter(lot=parking_lot, entry_time__date=today).count()
        entries_yesterday = ParkingRecord.objects.filter(lot=parking_lot, entry_time__date=yesterday).count()
        entries_last_7_days = ParkingRecord.objects.filter(lot=parking_lot, entry_time__gte=week_ago).count()
        total_entries = ParkingRecord.objects.filter(lot=parking_lot).count()

        context = dict(
            self.admin_site.each_context(request),
            parking_lot=parking_lot,
            #customers=customers,
            records=records,
            entries_today = entries_today,
            entries_yesterday = entries_yesterday,
            entries_last_7_days = entries_last_7_days,
            total_entries = total_entries,
            app_list = self.admin_site.get_app_list(request, app_label='projectApp'),
        )
        return render(request, 'admin/parkinglot_detail.html', context)
    

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'vehicle_number', 'contact_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(account__parking_lots__admin=request.user).distinct()
    
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_account', 'lot_name', 'reservation_time', 'reserved_date', 'reserved_from', 'reserved_to')

    def customer_account(self, obj):
        return obj.customer.account.username
    customer_account.short_description = 'Customer Account'

    def lot_name(self, obj):
        return obj.lot.name
    lot_name.short_description = 'Parking Lot'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(lot__admin=request.user).distinct()


class Payment_VNPayAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'order_id', 'amount', 'payment_date', 'payment_status']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(reservation__lot__admin=request.user).distinct()

    def payment_status(self, obj):
        if obj.vnp_response_code == '00':
            return "completed"
        else:
            return "failed"
    payment_status.short_description = 'Payment Status'

admin.site.register(Reservation, ReservationAdmin)
admin.site.register(ParkingLot, ParkingLotAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Payment_VNPay, Payment_VNPayAdmin)

admin.site.unregister(Group)

