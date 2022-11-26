from django.urls import path
from medimode.modules.catalogue import views

urlpatterns = [
	path('pharmacy/<int:pk>', views.PharmacyView.as_view(), name='pharmacy_view'),
	path('insurance/<int:pk>', views.InsuranceView.as_view(), name='insurance_details'),
	path('hospital/<int:pk>', views.HospitalView.as_view(), name='hospital_details'),
	path('doctor/<int:pk>', views.DoctorView.as_view(), name='doctor_details'),
	path('catalogue/<str:category>', views.Catalogue.as_view(), name='catalogue'),
	path('search', views.Search.as_view(), name='search'),
]
