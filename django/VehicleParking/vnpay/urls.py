from django.urls import path
from . import views

urlpatterns = [
    path('pay/', views.index, name='index'),
    path('payment/<int:reservation_id>/', views.payment, name='payment'),
    path('payment_ipn/', views.payment_ipn, name='payment_ipn'),
    path('payment_return/', views.payment_return, name='payment_return'),
    path('query/', views.query, name='query'),
    path('refund/', views.refund, name='refund'),
]
