from django.urls import path
from . import views

urlpatterns = [
    path('create-parking-record/', views.create_parking_record, name='create_parking_record'),
    path('update-availability/', views.update_availability, name='update_availability'),
    path('parking_spots/<int:lot_id>/', views.get_parking_spots, name='get_parking_spots'),
    path('rfid/', views.rfid_entry_exit, name='rfid_entry_exit'),
    path('parking_lots/', views.ParkingLotListView.as_view(), name='parking_lot_list'),
    path('spot_reserved/', views.SpotReservedView.as_view(), name='spot_reserved')
]
