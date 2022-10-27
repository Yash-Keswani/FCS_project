"""FCS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from medimode import views

urlpatterns = [
	path('', views.Home.as_view(), name='medimode_index'),
	
	path('catalogue/<str:category>', views.Catalogue.as_view(), name='catalogue'),
	
	path('pharmacy/<int:pk>', views.PharmacyView.as_view(), name='pharmacy_view'),
	path('insurance/<int:pk>', views.InsuranceView.as_view(), name='insurance_details'),
	path('hospital/<int:pk>', views.HospitalView.as_view(), name='hospital_details'),
	
	path('doctor/<int:pk>', views.DoctorView.as_view(), name='doctor_details'),
]
