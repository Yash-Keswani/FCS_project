from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, DetailView, ListView, CreateView

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable, Ticket, Profile, Ticket_Shareable

def verifyOTP(request):
	otp_given = request.POST.get("otp")
	otp_actual = request.user.totp
	return otp_given == otp_actual

class Home(LoginRequiredMixin, TemplateView):
	template_name = "medimode/home.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

class OTPSeed(TemplateView, LoginRequiredMixin):
	template_name = "medimode/my_seed.html"

class InsuranceView(LoginRequiredMixin, DetailView):
	login_url = '/medimode/login'
	model = Insurance

class DoctorView(LoginRequiredMixin, DetailView):
	login_url = '/medimode/login'
	model = Doctor

class PharmacyView(LoginRequiredMixin, DetailView):
	login_url = '/medimode/login'
	model = Pharmacy

class HospitalView(LoginRequiredMixin, DetailView):
	login_url = '/medimode/login'
	model = Hospital

class Catalogue(LoginRequiredMixin, ListView):
	login_url = '/medimode/login'
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


class ShareDocument(CreateView):
	login_url = '/medimode/login'
	model = Shareable
	fields = ['doc_file', 'filename', 'shared_with']
	success_url = reverse_lazy('medimode_index')
	
	def get_context_data(self):
		ctx = super().get_context_data()
		ctx['profiles'] = Profile.objects.exclude(user=self.request.user)
		return ctx
	
	def form_valid(self, form):
		form.instance.owner = self.request.user.profile
		return super().form_valid(form)

# noinspection PyMethodMayBeStatic
class IssueTicket(View):
	def get(self, request: HttpRequest):
		ctx = {
			'shareables': Shareable.objects.filter(owner=request.user.profile),
			'issued': Profile.objects.get(pk=int(request.GET.get('issued_to')))
		}
		return render(request, template_name="medimode/ticket_form.html", context=ctx)
	
	def post(self, request: HttpRequest):
		_issuer = request.user.profile
		_issued = Profile.objects.get(pk=request.POST.get("issued"))
		_description = request.POST.get("description")
		_otp = request.POST.get("otp")
		
		if not verifyOTP(request):
			pass	# raise ValidationError("Invalid OTP provided")
		
		tkt_shareables = []
		for _doc_file in request.FILES.getlist("doc_files"):
			tkt_shareable = Ticket_Shareable(doc_file=_doc_file, filename=_doc_file.name, owner=request.user.profile, party=Ticket_Shareable.PARTY.ISSUER)
			tkt_shareable.save()
			tkt_shareable.shared_with.add(_issued)
			tkt_shareable.save()
			tkt_shareables.append(tkt_shareable)
		"""
		_shareables = []
		if request.POST.get("shareables"):
			_shareables = [Shareable.objects.get(pk=x) for x in request.POST.get("shareables")]
		for shareable in _shareables:
			tkt_shareable = Ticket_Shareable(shareable_ptr_id=shareable.id)
			tkt_shareable.party = Ticket_Shareable.PARTY.ISSUER
			tkt_shareable.save_base(raw=True)
			tkt_shareable.shared_with.add(_issuer)
			tkt_shareables.append(tkt_shareable)
		"""
		tkt = Ticket(issuer=_issuer, issued=_issued, description=_description)
		tkt.save()
		tkt.shareables.add(*tkt_shareables)
		tkt.save()
		
		return redirect(to=reverse('issue_ticket'))

class MyTickets(ListView):
	def get_queryset(self):
		return Ticket.objects.filter(Q(issued=self.request.user.profile) | Q(issuer=self.request.user.profile))

class Login(LoginView):
	next_page = reverse_lazy("medimode_index")

class TicketView(LoginRequiredMixin, DetailView):
	login_url = '/medimode/login'
	template_name = "medimode/ticketDetail.html"
	model = Ticket