from .models import ParkingLot

def parking_lot_context_processor(request):
    if request.user.is_authenticated:
        parking_lots = ParkingLot.objects.filter(admin=request.user)
    else:
        parking_lots = ParkingLot.objects.none()
    
    return {
        'queryset': parking_lots
    }
