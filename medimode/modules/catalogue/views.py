import difflib
import json

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404, JsonResponse

from medimode.models import Insurance, Doctor, Pharmacy, Hospital
from medimode.modules.accounts.views import state_text
from medimode.sanitation_tools import str_to_model, get_clean
from medimode.views_base import AuthDetailView, AuthListView, AuthTemplateView

class InsuranceView(AuthDetailView):
	template_name = 'medimode/catalogue/insurance_detail.html'
	model = Insurance

class DoctorView(AuthDetailView):
	template_name = 'medimode/catalogue/doctor_detail.html'
	model = Doctor

class PharmacyView(AuthDetailView):
	template_name = 'medimode/catalogue/pharmacy_detail.html'
	model = Pharmacy

class HospitalView(AuthDetailView):
	template_name = 'medimode/catalogue/hospital_detail.html'
	model = Hospital

class Catalogue(AuthListView):
	template_name = "medimode/catalogue/catalogue_list.html"
	
	def get_queryset(self):
		cat = str_to_model(self.kwargs['category'])
		if cat is None:
			raise Http404()
		return cat.objects.all()
	
	def get_context_data(self, *, object_list=None, **kwargs):
		cat = str_to_model(self.kwargs['category'])
		
		ctx = super().get_context_data(object_list=object_list, kwargs=kwargs)
		ctx['model'] = self.kwargs['category'].title()
		ctx['model_plural'] = cat._meta.verbose_name_plural.title()
		ctx['is_org'] = (self.kwargs['category'] in ('hospital', 'pharmacy', 'insurance'))
		return ctx

class Search(AuthTemplateView):
	template_name = "medimode/catalogue/search.html"
	
	def get_context_data(self, **kwargs):
		ctx = super().get_context_data(**kwargs)
		ctx["state_json"] = state_text
		ctx["state_dict"] = json.loads(state_text)
		return ctx
	
	def post(self, request):
		category = str_to_model(request.POST.get("category"))
		entity_name = get_clean(request.POST, "entity_name")
		location_state = get_clean(request.POST, "state")
		location_city = get_clean(request.POST, "city")
		
		if not (request.POST.get("loc_search") or request.POST.get("name_search") or request.POST.get("search")):
			raise ValidationError("Invalid Search category")
		
		all_objs = category.objects.all()
		if request.POST.get("loc_search") or request.POST.get("search"):
			all_objs = category.objects.filter(Q(location_state=location_state) & Q(location_city=location_city))
			entries = [x.user for x in all_objs]
		
		if request.POST.get("name_search") or request.POST.get("search"):
			names_obj = {x.full_name: x.user for x in all_objs}
			
			entries_close = set([names_obj[x] for x in difflib.get_close_matches(entity_name, names_obj.keys(), n=10)])
			entries_including = set([names_obj[x] for x in names_obj if entity_name in x])
			
			entries = list(entries_close | entries_including)
		
		ctx = {"entries": [{"role": x.role, "name": x.profile.full_name, "bio": x.profile.bio, "id": x.profile.id} for x in entries]}
		return JsonResponse(data=ctx)
