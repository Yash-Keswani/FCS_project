from django.urls import path, include
from medimode import views

urlpatterns = [
	path('', include('medimode.modules.accounts.urls')),
	path('', include('medimode.modules.admin.urls')),
	path('', include('medimode.modules.api.urls')),
	path('', include('medimode.modules.catalogue.urls')),
	path('', include('medimode.modules.ticketing.urls')),
	path('', views.Home.as_view(), name='medimode_index'),
	path('my_documents', views.MyDocuments.as_view(), name='my_documents'),
	path('share_document', views.ShareDocument.as_view(), name='share_document'),
	

]

