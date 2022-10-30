from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views.generic import TemplateView, DetailView, ListView, CreateView

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable
from django.urls import reverse_lazy
from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable, User, Ticket, Profile, Ticket_Shareable

def verifyOTP(request):
	otp_given = request.POST.get("otp")
	otp_actual = request.user.totp
	return otp_given == otp_actual

class Home(LoginRequiredMixin,TemplateView):
	template_name = "medimode/home.html"
	login_url = '/medimode/login'
	redirect_field_name = ''
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

class OTPSeed(TemplateView, LoginRequiredMixin):
	template_name = "medimode/my_seed.html"

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
	success_url = reverse_lazy('medimode_index')

	def form_valid(self, form):
		form.cleaned_data['owner'] = self.request.user
		return super().form_valid(form)

# noinspection PyMethodMayBeStatic
class IssueTicket(View):
	def get(self, request: HttpRequest):
		ctx = {}
		ctx['shareables'] = Shareable.objects.filter(owner=request.user.profile)
		ctx['issued'] = Profile.objects.get(pk=int(request.GET.get('issued_to')))
		return render(request, template_name="medimode/ticket_form.html", context=ctx)
	
	def post(self, request: HttpRequest):
		_issuer = request.user.profile
		_issued = Profile.objects.get(pk=request.POST.get("issued"))
		_description = request.POST.get("description")
		_shareables = [Shareable.objects.get(pk=x) for x in request.POST.get("shareables")]
		_otp = request.POST.get("otp")
		if not verifyOTP(request):
			# raise ValidationError("Invalid OTP provided")
			pass
		
		tkt_shareables=[]
		for shareable in _shareables:
			tkt_shareable = Ticket_Shareable(shareable_ptr_id=shareable.id)
			tkt_shareable.party = Ticket_Shareable.PARTY.ISSUER
			tkt_shareable.save_base(raw=True)
			tkt_shareables.append(tkt_shareable)
		tkt = Ticket(issuer=_issuer, issued=_issued, description=_description)
		tkt.save()
		tkt.shareables.add(*tkt_shareables)
		tkt.save()
		
		return render(request, reverse('issue_ticket'))
		
class Login(LoginView):
	next_page = reverse_lazy("medimode_index")
