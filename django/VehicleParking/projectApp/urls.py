from django.urls import path
from . import views


urlpatterns = [
    path('', views.router, name="router"),
    path("home/", views.home, name="home"),

    #customer
    path('complete-profile/', views.customer_info, name='profile'),
    
    #reservation
    path('reservation/', views.user_reservation_list, name='reservation_history'),
    path('create-reservation/<int:pk>/', views.create_reservation, name='create_reservation'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='reservation_detail'),
    path('reservation_success/<int:reservation_id>/', views.reservation_success, name='reservation_success'),
    path('no-permission/', views.no_permission, name='no_permission'),
    path('cancel/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
]

