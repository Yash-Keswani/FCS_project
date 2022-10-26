from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

class MedimodeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medimode'
		
class MedimodeAdminConfig(AdminConfig):
    default_site = 'medimode.admin.MyAdminSite'
