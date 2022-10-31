from django.urls import path, include

from mypay import views

urlpatterns = [
	path('', views.Home.as_view(), name='mypay_index'),
	path('make_payment', views.MakePayment.as_view(), name='make_payment'),
	path('success', views.transaction_success, name='success'),
	path('failure', views.transaction_failure, name='failure')
]
