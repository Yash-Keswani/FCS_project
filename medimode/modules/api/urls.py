from django.urls import path
from medimode.modules.api import views

urlpatterns = [
	path('media/delete/<path:filepath>', views.delete_media, name='delete_media'),
	path('media/verify/<path:filepath>', views.verify_fetch_media, name='verified_media'),
	path('media/private/<path:filepath>', views.ProfileFileView.as_view(), name='private_media'),
	path('media/<path:filepath>', views.fetch_media, name='fetch_media'), # TODO: deprecate this
]
