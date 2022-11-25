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
	
	path('approve_users', views.ApproveUsers.as_view(), name='approve_users'),
	path('remove_users', views.RemoveUsers.as_view(), name='remove_users'),
	path('user_documents', views.Documents.as_view(), name='user_documents'),
	path('search', views.Search.as_view(), name='search'),
	
	path('login', views.Login.as_view(), name='login'),
	path('signup/org', views.SignupOrg.as_view(), name='signup_org'),
	path('signup/individual', views.SignupIndividual.as_view(), name='signup_individual'),
	
	path('myseed', views.OTPSeed.as_view(), name='seed'),
	path('my_tickets', views.MyTickets.as_view(), name='my_tickets'),
	path('my_documents', views.MyDocuments.as_view(), name='my_documents'),
	
	path('catalogue/<str:category>', views.Catalogue.as_view(), name='catalogue'),
	
	path('pharmacy/<int:pk>', views.PharmacyView.as_view(), name='pharmacy_view'),
	path('insurance/<int:pk>', views.InsuranceView.as_view(), name='insurance_details'),
	path('hospital/<int:pk>', views.HospitalView.as_view(), name='hospital_details'),
	
	path('doctor/<int:pk>', views.DoctorView.as_view(), name='doctor_details'),
	
	path('share_document', views.ShareDocument.as_view(), name='share_document'),
	path('ticket/<int:pk>', views.TicketView.as_view(), name='ticket_view'),
	path('issue_ticket', views.IssueTicket.as_view(), name='issue_ticket'),
	
	path('media/delete/<path:filepath>', views.delete_media, name='delete_media'),
	path('media/verify/<path:filepath>', views.verify_fetch_media, name='verified_media'),
	path('media/<path:filepath>', views.fetch_media, name='fetch_media'),

	path('previousBills', views.MyTicketsforBills.as_view(), name='my_ticketsBills'),
	

	
]
