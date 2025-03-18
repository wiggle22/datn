from django.urls import path
from django.conf.urls import handler404  # Import handler404 from django.conf.urls
from . import views

urlpatterns = [
    path('signup/completed', views.completed, name='signup'),
    path('signup/form', views.signup, name='signup'),
    path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$', views.activate, name='activate'),
]

# Define a custom 404 handler
# handler404 = views.custom_404
handler404 = 'signup.views.custom_404'

