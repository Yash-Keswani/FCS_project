from django.urls import path, include

from mypay import views

urlpatterns = [
	path('', views.Home.as_view(), name='mypay_index')
]
