from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView, DetailView, ListView, CreateView

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable
from django.urls import reverse_lazy

class Home(LoginRequiredMixin,TemplateView):
	template_name = "medimode/home.html"
	login_url = '/medimode/login'
	redirect_field_name = ''
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

class InsuranceView(LoginRequiredMixin,DetailView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	model = Insurance

class DoctorView(LoginRequiredMixin,DetailView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	model = Doctor

class PharmacyView(LoginRequiredMixin,DetailView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	model = Pharmacy

class HospitalView(LoginRequiredMixin,DetailView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	model = Hospital
	
class Catalogue(LoginRequiredMixin,ListView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	template_name = "medimode/catalogue_list.html"
	model_mapping = {"hospital": Hospital, "pharmacy": Pharmacy, "insurance": Insurance, "doctor": Doctor}
	
	def get_queryset(self):
		cat = self.model_mapping.get(self.kwargs['category'])
		if cat is None:
			raise Http404()
		return cat.objects.all()
	
	def get_context_data(self, *, object_list=None, **kwargs):
		cat = self.model_mapping.get(self.kwargs['category'])
		
		ctx = super().get_context_data(object_list=object_list, kwargs=kwargs)
		ctx['model'] = self.kwargs['category'].title()
		ctx['model_plural'] = cat._meta.verbose_name_plural.title()
		ctx['is_org'] = (self.kwargs['category'] in ('hospital', 'pharmacy', 'insurance'))
		return ctx
	
class ShareDocument(LoginRequiredMixin,CreateView):
	login_url = '/medimode/login'
	redirect_field_name = ''
	model = Shareable
	fields = ['doc_file', 'filename', 'shared_with']

	def form_valid(self, form):
		form.cleaned_data['owner'] = self.request.user
		return super().form_valid(form)

class Login(LoginView):
	next_page=reverse_lazy("medimode_index");
	pass
