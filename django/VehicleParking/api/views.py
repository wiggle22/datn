from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from projectApp.models import ParkingLot, ParkingRecord, ParkingSpot
from datetime import timedelta
import json
from django.utils import timezone
from django.views import View
from geopy.distance import distance

@api_view(['POST'])
def create_parking_record(request):
    try:
        lot_id = request.data.get('lot_id')
        lot = ParkingLot.objects.get(id=lot_id)

        # Create a new ParkingRecord for the lot
        ParkingRecord.objects.create(lot=lot)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)

        # Lấy số lần entry của lot trong hôm nay
        entries_today = ParkingRecord.objects.filter(lot=lot, entry_time__date=today).count()

        # Lấy số lần entry của lot trong hôm qua
        entries_yesterday = ParkingRecord.objects.filter(lot=lot, entry_time__date=yesterday).count()

        # Lấy số lần entry của lot trong 7 ngày gần nhất
        entries_last_7_days = ParkingRecord.objects.filter(lot=lot, entry_time__gte=week_ago).count()

        # Lấy số lần entry của lot tổng cộng
        total_entries = ParkingRecord.objects.filter(lot=lot).count()

        return JsonResponse({
            'lot_id': lot_id,
            'entries_today': entries_today,
            'entries_yesterday': entries_yesterday,
            'entries_last_7_days': entries_last_7_days,
            'total_entries': total_entries,
        })
    except ParkingLot.DoesNotExist:
        return JsonResponse({"error": "Parking lot not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
    
    
@api_view(['POST'])
def update_availability(request):
    try:
        lot_id = request.data.get('lot_id')
        status = request.data.get('is_available')
        spot_avaiable = json.loads(request.data.get('sensorsWithOne'))

        spot_avaiable = [spot + 1 for spot in spot_avaiable]
        ParkingSpot.objects.filter(lot_id=lot_id).update(is_avaiable=False)
        ParkingSpot.objects.filter(lot_id=lot_id, spot_number__in=spot_avaiable).update(is_avaiable=True)

        lot = ParkingLot.objects.get(id=lot_id)
        if status == 'full':
            lot.is_available = False
        else:
            lot.is_available = True

        lot.save()

        return JsonResponse({
            'lot_id': lot_id,
            'is_available': lot.is_available,
            'spot_avaiable': spot_avaiable,
        })
    except ParkingLot.DoesNotExist:
        return JsonResponse({"error": "Parking lot not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@api_view(['GET'])
def get_parking_spots(request, lot_id):
    try:
        parking_lot = ParkingLot.objects.get(id=lot_id)
        spots = ParkingSpot.objects.filter(lot=parking_lot)
        spots_data = [
            {
                'id': spot.id,
                'spot_number': spot.spot_number,
                'is_reserved': spot.is_reserved,
                'is_avaiable': spot.is_avaiable,
            }
        for spot in spots]
        total_available_spots = spots.filter(is_avaiable=True, is_reserved=False).count()

        return Response({
            'spots': spots_data,
            'total_available_spots': total_available_spots,
        })
    except ParkingLot.DoesNotExist:
        return Response({"error": "Parking lot not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

class SpotReservedView(View):
    def get(self, request):
        lot = request.GET.get('lot_id')

        lot = ParkingLot.objects.get(id=lot)
        reserved_spots = ParkingSpot.objects.filter(lot=lot, is_reserved=True)
        spot_reserved = []
        for spot in reserved_spots:
            spots = spot.spot_number
            spot_reserved.append(spots)
        return JsonResponse({
            'spot_reserved': spot_reserved
        })


@api_view(['POST'])
def rfid_entry_exit(request):
    try:
        data = json.loads(request.body)
        rfid_code = data.get('rfid_code')
        lot_id = data.get('lot_id')
        entry_type = data.get('type')  # Get the type of entry (entry or exit)

        # Tìm ParkingLot dựa trên lot_id
        lot = ParkingLot.objects.get(id=lot_id)

        # Kiểm tra số bản ghi vào không có bản ghi ra
        entry_without_exit_count = ParkingRecord.objects.filter(lot=lot, exit_time__isnull=True).count()

        if entry_type == "entry":
            if not lot.is_available or entry_without_exit_count >= 10:
                return JsonResponse({'status': 'lot not available'}, status=400)

            # Kiểm tra nếu có bất kỳ bản ghi entry nào chưa có exit
            existing_record = ParkingRecord.objects.filter(lot=lot, rfid_code=rfid_code, exit_time__isnull=True).exists()
            if existing_record:
                return JsonResponse({'status': 'entry already recorded'}, status=400)
            
            # Tạo bản ghi mới khi là entry
            record = ParkingRecord.objects.create(lot=lot, rfid_code=rfid_code, entry_time=timezone.now())
            entry_time = record.entry_time.strftime('%Y-%m-%d %H:%M:%S')
                
            return JsonResponse({'status': 'entry recorded', 'entry_time': entry_time})
        elif entry_type == "exit":
            # Tìm ParkingRecord có exit_time là None và rfid_code
            record = ParkingRecord.objects.filter(lot=lot, rfid_code=rfid_code, exit_time__isnull=True).first()
            if record:
                # Nếu tồn tại, cập nhật exit_time
                record.exit_time = timezone.now()
                record.save()
                exit_time = record.exit_time.strftime('%Y-%m-%d %H:%M:%S')
                entry_time = record.entry_time.strftime('%Y-%m-%d %H:%M:%S')
                fee = record.calculate_fee()
                
                return JsonResponse({'status': 'exit recorded', 'entry_time': entry_time, 'exit_time': exit_time, 'fee': fee, 'rfid_code': rfid_code})
            else:
                return JsonResponse({'status': 'no entry record found'}, status=400)
        else:
            return JsonResponse({'status': 'invalid entry type'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    


class ParkingLotListView(View):
    def get(self, request):
        user_lat = float(request.GET.get('latitude', 0))
        user_lng = float(request.GET.get('longitude', 0))
        search_query = request.GET.get('search', '')

        parking_lots = ParkingLot.objects.all()

        if search_query:
            parking_lots = parking_lots.filter(
                name__icontains=search_query
            )

        parking_lots_with_distance = []

        for lot in parking_lots:
            lot_distance = distance((user_lat, user_lng), (lot.latitude, lot.longitude)).km
            parking_lots_with_distance.append({
                'id': lot.id,
                'name': lot.name,
                'location': lot.location,
                'opening_time': lot.formatted_opening_time(),
                'closing_time': lot.formatted_closing_time(),
                'price_for_first_two_hours': lot.formatted_price_for_first_two_hours(),
                'price_per_hour_after_two_hours': lot.formatted_price_per_hour_after_two_hours(),
                'total_capacity': lot.total_capacity,
                'latitude': lot.latitude,
                'longitude': lot.longitude,
                'image_url': lot.image.url if lot.image else '',
                'distance': lot_distance,
            })

        parking_lots_with_distance.sort(key=lambda x: x['distance'])

        return JsonResponse(parking_lots_with_distance, safe=False)