from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from math import ceil
from PIL import Image
from datetime import timedelta, datetime


# Create your models here.
class Customer(models.Model):
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    full_name = models.CharField(max_length=100, blank=True)
    vehicle_number = models.CharField(max_length=20)
    registration_date = models.DateField()
    contact_number = models.CharField(max_length=20)

    def __str__(self):
        return self.account.username



class ParkingLot(models.Model):
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parking_lots', null=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    price_for_first_two_hours = models.IntegerField(default=0)
    price_per_hour_after_two_hours = models.IntegerField()
    total_capacity = models.PositiveIntegerField(unique=False)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='parking_lot_images/', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('admin:parkinglot_details', args=[self.pk])
    
    def formatted_price_for_first_two_hours(self):
        return f'{self.price_for_first_two_hours:,.0f} VNĐ'
    
    def formatted_price_per_hour_after_two_hours(self):
        return f'{self.price_per_hour_after_two_hours:,.0f} VNĐ'
    
    def formatted_opening_time(self):
        return self.opening_time.strftime('%I:%M %p').upper()
    
    def formatted_closing_time(self):
        return self.closing_time.strftime('%I:%M %p').upper()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)
        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

class ParkingSpot(models.Model):
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spots')
    spot_number = models.CharField(max_length=10)
    is_reserved = models.BooleanField(default=False)
    is_avaiable = models.BooleanField(default=False)

    def __str__(self):
        return f"Spot {self.spot_number} in {self.lot.name}"

class ParkingRecord(models.Model):
    lot = models.ForeignKey(ParkingLot, related_name='records', on_delete=models.CASCADE)
    rfid_code = models.CharField(max_length=100, default='default_rfid_code')
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.lot.name} - RFID: {self.rfid_code} - Entry: {self.entry_time}, Exit: {self.exit_time}"
    
    def calculate_fee(self):
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            hours = duration.total_seconds() / 3600
            if hours <= 2:
                total_price = 1 * self.lot.price_for_first_two_hours
            else:
                total_price = (1 * self.lot.price_for_first_two_hours) + ((hours - 2) * self.lot.price_per_hour_after_two_hours)
            return total_price
        return 0
    
    def calculate_fee_reserved(self):
        if self.exit_time:
            duration = self.exit_time - self.entry_time
            hours = duration.total_seconds() / 3600
            if hours > 2:
                total_price = ((hours - 2) * self.lot.price_per_hour_after_two_hours)
                return total_price
            else:
                return 0
            
        
    

    
class Reservation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='reservations')
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='reservations')
    spot = models.ForeignKey(ParkingSpot, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    reservation_time = models.DateTimeField(default=timezone.now)
    reserved_date = models.DateField(null=True, auto_now_add=True)
    reserved_from = models.TimeField()
    reserved_to = models.TimeField()
    is_paid = models.BooleanField(default=False)
    qr_code_scanned = models.CharField(max_length=20, null=True)
    is_cancelled = models.BooleanField(default=False)

    def __str__(self):
        return f"Reservation for {self.customer.full_name} on {self.reserved_date} from {self.reserved_from} to {self.reserved_to}"

    def get_download_url(self):
        return reverse('download_reservation', args=[self.id])
    
    def calculate_total_price(self):
        total_hours = (self.reserved_to.hour * 60 + self.reserved_to.minute - self.reserved_from.hour * 60 - self.reserved_from.minute) / 60
        rounded_hours = ceil(total_hours)
        if rounded_hours <= 2:
            total_price = 1 * self.lot.price_for_first_two_hours
        else:
            total_price = (1 * self.lot.price_for_first_two_hours) + ((rounded_hours - 2) * self.lot.price_per_hour_after_two_hours)
        return total_price
    
    @property
    def can_cancel(self):
        now = timezone.now()
        # Tạo đối tượng datetime từ reserved_date và reserved_from để sử dụng timedelta
        reserved_datetime = datetime.combine(self.reserved_date, self.reserved_from)
        cancel_deadline_end = reserved_datetime - timedelta(minutes=1)
        return now <= cancel_deadline_end

    @property
    def is_past_cancel_time(self):
        now = timezone.now()
        reserved_datetime = datetime.combine(self.reserved_date, self.reserved_from)
        cancel_deadline_end = reserved_datetime - timedelta(minutes=1)
        return now > cancel_deadline_end
    


class Payment_VNPay(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='payment')
    order_id = models.IntegerField(max_length=100, null=True)
    amount = models.IntegerField()
    payment_date = models.DateTimeField(auto_now_add=True)
    vnp_transaction_no = models.CharField(max_length=8)
    vnp_response_code = models.CharField(max_length=2)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.vnp_response_code == 00:
            self.reservation.is_paid = True
            self.reservation.save()



class TemporaryData(models.Model):
    reservation_id = models.IntegerField()  # Điều chỉnh kiểu dữ liệu tùy thuộc vào kiểu dữ liệu của reservation_id trong model Reservation
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Temporary Data (ID: {self.id}, Reservation ID: {self.reservation_id})"