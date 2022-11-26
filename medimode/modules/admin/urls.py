from django.urls import path
from medimode.modules.admin import views

urlpatterns = [
	path('approve_users', views.ApproveUsers.as_view(), name='approve_users'),
	path('remove_users', views.RemoveUsers.as_view(), name='remove_users'),
	path('user_documents', views.Documents.as_view(), name='user_documents'),
]
