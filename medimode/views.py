from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import UpdateView

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable, Ticket, Profile, Ticket_Shareable, User
from medimode.views_base import AuthTemplateView, AuthDetailView, AuthListView, AuthCreateView

#>> FUNCTIONS <<#
def verifyOTP(request):
	otp_given = request.POST.get("otp")
	otp_actual = request.user.totp
	return otp_given == otp_actual

#>> PUBLIC VIEWS <<#
class Login(LoginView):
	next_page = reverse_lazy("medimode_index")
	
#>> ADMIN VIEWS <<#
class ApproveUsers(AuthListView):
	template_name = "medimode/approve_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=False)
	
	def post(self, request):
		approved_users = request.POST.get("approved_users")
		approved_profiles = [Profile.objects.get(pk=x) for x in approved_users]
		
		for profile in approved_profiles:
			profile.approved = True
			profile.save()
		
		return redirect(reverse('approve_users'))

class RemoveUsers(AuthListView):
	template_name = "medimode/reject_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=True)
	
	def post(self, request):
		approved_users = request.POST.get("approved_users")
		approved_profiles = [Profile.objects.get(pk=x) for x in approved_users]
		
		for profile in approved_profiles:
			profile.approved = False
			profile.save()
		
		return redirect(reverse('remove_users'))
	
#>> LOGIN RESTRICTED VIEWS <<#
class Home(AuthTemplateView):
	template_name = "medimode/home.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

class OTPSeed(AuthTemplateView):
	template_name = "medimode/my_seed.html"

class InsuranceView(AuthDetailView):
	model = Insurance

class DoctorView(AuthDetailView):
	model = Doctor

class PharmacyView(AuthDetailView):
	model = Pharmacy

class HospitalView(AuthDetailView):
	model = Hospital

class Catalogue(AuthListView):
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

class MyDocuments(AuthListView):
	model = Shareable

def delete_media(request, filepath):
	file = get_object_or_404(Shareable, doc_file=filepath)
	if request.user.profile == file.owner:
		file.delete()
		return redirect(to=reverse('my_documents'))
	else:
		return HttpResponseForbidden()

def fetch_media(request, filepath):
	file = get_object_or_404(Shareable, doc_file=filepath)
	if request.user.profile in file.shared_with.all() or request.user.profile == file.owner:
		return FileResponse(file.doc_file)
	else:
		return HttpResponseForbidden()
		
class ShareDocument(AuthCreateView):
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
			raise ValidationError("Invalid OTP provided")
		
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

class MyTickets(AuthListView):
	def get_queryset(self):
		return Ticket.objects.filter(Q(issued=self.request.user.profile) | Q(issuer=self.request.user.profile))

class TicketView(AuthDetailView):
	template_name = "medimode/ticketDetail.html"

	def get_context_data(self, **kwargs):
		return {"object": get_object_or_404(Ticket, self.request.GET.get("pk"))}
	
	def post(self, request):
		_money = request.POST.get("money")
		_req = request.POST.get("moneyreq")
		
		if _req and _money:
			payer, paid = (1,2)
	