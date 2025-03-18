from django.shortcuts import render, redirect
from .forms import CustomerForm, ReservationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from .models import Customer
from .models import Reservation, ParkingRecord, ParkingSpot
import qrcode
from io import BytesIO
import base64
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .models import ParkingLot
from datetime import timedelta, datetime
import requests
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives



@login_required
def customer_info(request):
    try:
        customer = Customer.objects.get(account=request.user)
        form = CustomerForm(instance=customer)
        if request.method == 'POST':
            form = CustomerForm(request.POST, instance=customer)
            if form.is_valid():
                form.save()
                return redirect('home')
    except Customer.DoesNotExist:
        form = CustomerForm(request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                customer = form.save(commit=False)
                customer.account = request.user
                # Lấy ngày tham gia của người dùng và gán cho trường registration_date
                customer.registration_date = request.user.date_joined.date()
                customer.save()
                return redirect('home')

    return render(request, 'customer/customer_info.html', {'form': form})

@login_required
def router(request):
    loaded = Customer.objects.filter(account=request.user.pk).first()
    if loaded is None:
        return HttpResponseRedirect('/accounts/complete-profile')
    else:
        return HttpResponseRedirect('/accounts/home')
    
def home(request):
    parking_lots = ParkingLot.objects.all()
    
    context = {
        'parking_lots': parking_lots
    }
    return render(request, 'home.html', context)

# Reservation
def check_and_update_spot_status():
    now = timezone.now()
    two_hours_ago = now - timedelta(hours=2)
    # Tạo một đối tượng datetime với thông tin ngày và giờ
    # Chú ý: Bạn cần chỉ rõ timezone để tránh nhầm lẫn về múi giờ
    reservations_to_update = Reservation.objects.filter(
        qr_code_scanned__isnull=True,  # Chưa được check-in
        reserved_from__lt=two_hours_ago.time(),  # Quá thời gian đặt chỗ + 2 giờ
        spot__is_reserved=True,  # Đang được đặt chỗ
        is_paid=True,
    )

    for reservation in reservations_to_update:
        reservation.spot.is_reserved = False
        reservation.qr_code_scanned = 'not_come'
        reservation.save()
        reservation.spot.save()


def create_reservation(request, pk):
    check_and_update_spot_status()
    parking_lot = get_object_or_404(ParkingLot, pk=pk)
    reservation_valid = True
    all_spots = parking_lot.spots.all()
    now = timezone.now()

    if request.method == 'POST':
        form = ReservationForm(request.POST, lot=parking_lot)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.customer = Customer.objects.get(account=request.user)
            reservation.lot = parking_lot
            
            # Kiểm tra thời gian đặt chỗ nằm trong khoảng thời gian mở cửa
            opening_time = reservation.reserved_from.replace(hour=parking_lot.opening_time.hour, minute=parking_lot.opening_time.minute)
            closing_time = reservation.reserved_from.replace(hour=parking_lot.closing_time.hour, minute=parking_lot.closing_time.minute)
            if (not (opening_time <= reservation.reserved_from <= closing_time) or not ((now + timedelta(minutes=30)).time() <= reservation.reserved_from <= (now + timedelta(hours=2)).time())):
                reservation_valid = 'False_in'
            else:
                # Kiểm tra thời gian đặt chỗ ra sau thời gian đóng cửa
                if reservation.reserved_to > closing_time or reservation.reserved_to <= reservation.reserved_from:
                    reservation_valid = 'False_out'
                else:
                    reservation.save()

                    # Chuyển hướng đến trang xác nhận thanh toán
                    return redirect(reverse('payment', args=[reservation.id]))
    else:
        form = ReservationForm(lot=parking_lot)
    return render(request, 'reservation/create_reservation.html', {
        'parking_lot': parking_lot,
        'form': form,
        'reservation_valid': reservation_valid,
        'all_spots': all_spots
    })


def reservation_success(request, reservation_id):
    now = timezone.now()
    reservation = get_object_or_404(Reservation, id=reservation_id)
    if not reservation.is_paid:
        now = timezone.now()
        reserved_from_datetime = datetime.combine(now.date(), reservation.reserved_from)
        ineligible_time = reserved_from_datetime - timedelta(minutes=30)

        # Kiểm tra nếu đã quá thời gian cho phép và chưa thanh toán
        if now >= ineligible_time:
            context = {
                'reservation': reservation,
                'payment_timeout': True,
                'message': "Quá thời hạn thanh toán"
            }
            return render(request, 'reservation/reservation_success.html', context)
        # Nếu chưa quá thời gian cho phép, chuyển hướng đến trang thanh toán
        return redirect(reverse('payment', args=[reservation.id]))
    
    # Tạo thời gian hết hạn
    reserved_from_datetime = datetime.combine(reservation.reserved_date, reservation.reserved_from)
    expiration_time = reserved_from_datetime + timedelta(hours=2)
    expiration_timestamp = int(expiration_time.timestamp())

    # Generate QR code with URL to reservation detail page and expiration timestamp
    reservation_url = request.build_absolute_uri(reverse('reservation_detail', args=[reservation.id]))
    qr_data = f"{reservation_url}?expires={expiration_timestamp}&valid_from={reserved_from_datetime.timestamp()}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render(request, 'reservation/reservation_success.html', {'reservation': reservation, 'qr_code': img_str})

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin, login_url='accounts/no-permission/')  # Thay thế '/no-permission/' bằng URL bạn muốn chuyển hướng khi không có quyền truy cập
def reservation_detail(request, reservation_id):
    expires = request.GET.get('expires')
    valid_from = request.GET.get('valid_from')

    # Kiểm tra thời gian hết hạn từ query parameters
    if expires:
        expiration_time = datetime.fromtimestamp(int(expires))
        print(expiration_time)
        if timezone.now() > expiration_time:
            return render(request, 'reservation/expired.html')
    
    # Kiểm tra thời gian bắt đầu hợp lệ từ query parameters (nếu có)
    if valid_from:
        valid_from_time = datetime.fromtimestamp(float(valid_from))
        if timezone.now() < valid_from_time:
            return render(request, 'reservation/not_yet_valid.html')

    reservation = get_object_or_404(Reservation, id=reservation_id)
    spot = reservation.spot.spot_number
    rfid_code = f"đặt chỗ vị trí {spot}"
    if reservation.qr_code_scanned == 'check_in':
        reservation.qr_code_scanned = 'check_out'
        record = ParkingRecord.objects.filter(lot=reservation.lot, rfid_code=rfid_code, exit_time__isnull=True).first()
        spot_record = ParkingSpot.objects.filter(lot=reservation.lot, spot_number=spot).first()
        if record:
            # Nếu tồn tại, cập nhật exit_time
            record.exit_time = timezone.now()
            record.save()

            if spot_record:
                spot_record.is_reserved = False
                spot_record.save()

            exit_time = record.exit_time.strftime('%Y-%m-%d %H:%M:%S')
            entry_time = record.entry_time.strftime('%Y-%m-%d %H:%M:%S')
            fee = record.calculate_fee_reserved()
            data_to_send = {
                'status': 'exit recorded',
                'entry_time': entry_time,
                'exit_time': exit_time,
                'fee': fee,
                'rfid_code': rfid_code
            }
        else:
            data_to_send = {'status': 'no entry record found'}

    elif reservation.qr_code_scanned == 'check_out':
        data_to_send = {'status': 'you dont have permission to entry'}

    else:
        reservation.qr_code_scanned = 'check_in'
        record = ParkingRecord.objects.create(lot=reservation.lot, rfid_code=rfid_code, entry_time=timezone.now())
        entry_time = record.entry_time.strftime('%Y-%m-%d %H:%M:%S')        
        data_to_send = {'status': 'entry recorded', 'entry_time': entry_time, 'rfid_code': rfid_code}

    reservation.save()

    # Send POST request to ESP32
    send_post_to_esp32(data_to_send)

    return render(request, 'reservation/reservation_detail.html', {'reservation': reservation})

def send_post_to_esp32(data):
    url = 'http://192.168.1.10/api/esp32_handler'
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("POST request sent to ESP32 successfully")
        else:
            print(f"Failed to send POST request to ESP32. Status code: {response.status_code}")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")

def user_reservation_list(request):
    # Kiểm tra người dùng đã đăng nhập hay chưa
    if request.user.is_authenticated:
        # Lấy danh sách đặt chỗ của người dùng đã đăng nhập và sắp xếp theo thứ tự mới nhất đến cũ nhất
        user_reservations = Reservation.objects.filter(customer=request.user.customer).order_by('-reservation_time')
        
        # Tạo Paginator với 5 đặt chỗ mỗi trang
        paginator = Paginator(user_reservations, 3)
        page = request.GET.get('page')
        
        try:
            reservations = paginator.page(page)
        except PageNotAnInteger:
            reservations = paginator.page(1)
        except EmptyPage:
            reservations = paginator.page(paginator.num_pages)
        
        # Dữ liệu gửi tới template
        context = {'user_reservations': reservations}
        
        # Render template và trả về HTTP response
        return render(request, 'reservation/reservation_list.html', context)
    else:
        return redirect('login')

def no_permission(request):
    return render(request, 'reservation/no_permission.html')

@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    
    # Kiểm tra xem thời điểm hủy vé có nằm trong khoảng 8:45 đến 8:59 không
    now = timezone.now()
    reserved_datetime = datetime.combine(reservation.reserved_date, reservation.reserved_from)
    cancel_deadline_end = reserved_datetime - timedelta(minutes=1)
    
    if now <= cancel_deadline_end:
        # Hủy vé và gửi email hoàn tiền
        reservation.is_cancelled = True
        reservation.save()
        reservation.spot.is_reserved = False
        reservation.spot.save()

        # Tính toán số tiền hoàn lại
        refund_amount = reservation.calculate_total_price() * 0.7

        # Gửi email thông báo hoàn tiền
        subject = 'Refund Confirmation'
        html_message = render_to_string('reservation/refund_email.html', {
            'reservation': reservation,
            'refund_amount': "{:,.0f}".format(refund_amount),
        })
        plain_message = strip_tags(html_message)
        from_email = settings.EMAIL_HOST_USER
        to_email = [request.user.email]

        email = EmailMultiAlternatives(subject, plain_message, from_email, to_email)
        email.attach_alternative(html_message, "text/html")
        email.send()

        # Redirect về trang lịch sử đặt vé
        return redirect('reservation_history')
    else:
        # Không thể hủy vé do đã quá thời gian cho phép
        return render(request, 'reservation/cancel_not_allowed.html')