from functools import lru_cache

from django.contrib import admin
from django.contrib.admin import AdminSite

from .models import Profile, Individual, Doctor, Patient, Hospital, Pharmacy, Insurance, Document, Organisation,\
	Transaction, Ticket, Shareable, Ticket_Shareable, User

# Register your models here.
model_hierarchy ={
	"Base": [User, Profile],
	"Individual": [Doctor, Patient],
	"Organistaion": [Hospital, Pharmacy, Insurance],
	"Documents": [Document, Shareable, Ticket_Shareable],
	"Interaction": [Ticket, Transaction]
}

class MyAdminSite(AdminSite):
	@lru_cache
	def get_app_list(self, request, app_label=None):
		temp_up = super().get_app_list(request, app_label)
		temp_down = []
		for app_reg in temp_up:
			if app_reg['name'] != 'Medimode':
				temp_down.append(app_reg)
			else:
				for app, models in model_hierarchy.items():
					temp_down.append({'name': app, 'app_label': app, 'app_url': '/admin/medimode', 'has_module_perms': True})
					models_list = []
					for model_target in models:
						for model_dict in app_reg['models']:
							if model_target == model_dict['model']:
								models_list.append(model_dict)
					temp_down[-1]["models"] = models_list
		return temp_down

admin.site = MyAdminSite()

for model_list in model_hierarchy.values():
	for model in model_list:
		admin.site.register(model)
		