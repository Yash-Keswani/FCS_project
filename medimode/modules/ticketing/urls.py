from django.urls import path

from medimode.modules.ticketing import views

urlpatterns = [
	path('my_tickets', views.MyTickets.as_view(), name='my_tickets'),
	path('ticket/<int:pk>', views.TicketView.as_view(), name='ticket_view'),
	path('issue_ticket', views.IssueTicket.as_view(), name='issue_ticket'),
	path('pay/<int:pk>', views.MakePayment.as_view(), name='pay'),
	path('previousBills', views.MyTicketsforBills.as_view(), name='my_ticketsBills'),
]
