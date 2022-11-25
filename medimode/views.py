import difflib
import hashlib

import magic
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404, FileResponse, HttpResponseForbidden, HttpResponse
from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable, Ticket, Profile, Ticket_Shareable, \
	Organisation, User, Patient, Document
from medimode.views_base import AuthTemplateView, AuthDetailView, AuthListView, AuthCreateView, AdminListView

# >> FUNCTIONS << #
def verifyOTP(request):
	otp_given = request.POST.get("otp")
	otp_actual = request.user.totp
	return otp_given == otp_actual
	
model_mapping = {"hospital": Hospital, "pharmacy": Pharmacy, "insurance": Insurance, "doctor": Doctor}
def str_to_model(model_name):
	return model_mapping.get(model_name)

# >> PUBLIC VIEWS << #
class Login(LoginView):
	next_page = reverse_lazy("medimode_index")
	
class SignupOrg(TemplateView):
	template_name = "medimode/signup/org.html"
	
	def get(self, request):
		return render(request, 'medimode/signup/org.html',
									{"form": modelform_factory(Organisation, exclude=[])})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		_username = _post.get('username')
		_password= _post.get('password')
		_bio= _post.get('bio')
		_contact= _post.get('contact_number')
		_image0= _files.get('image0')
		_image1= _files.get('image1')
		_location= _post.get('location')
		
		tomake = str_to_model(_post.get("model"))
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password, role=_post.get('model'))
		_model = tomake.objects.create(bio=_bio, user=_user, contact_number=_contact, image0=_image0, image1=_image1, location=_location)
		return redirect(reverse('login'))

class SignupIndividual(TemplateView):
	template_name = "medimode/signup/individual.html"
	
	def get(self, request):
		return render(request, 'medimode/signup/individual.html',
									{"form": modelform_factory(Organisation, exclude=[])})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		_username = _post.get('username')
		_password= _post.get('password')
		_bio= _post.get('bio')
		_poa = _files.get('proof_of_address')
		_proof_of_address= Document.objects.create(doc_file=_poa, filename=_poa.name)
		_poi= _files.get('proof_of_identity')
		_proof_of_identity= Document.objects.create(doc_file=_poi, filename=_poi.name)
		
		_med_doc= _files.get('medical_documents')
		if _med_doc!=None:
			_medical_documents = Document.objects.create(doc_file=_med_doc, filename=_med_doc.name)
		else:
			_medical_documents = None	
		
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password, role='Patient')
		_user.save()
		_model = Patient.objects.create(user=_user, bio=_bio, proof_of_address=_proof_of_address, proof_of_identity=_proof_of_identity, medical_info=_medical_documents)
		_model.save()
		return redirect(reverse('login'))
	
# >> ADMIN VIEWS << #
class ApproveUsers(AdminListView):
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

class RemoveUsers(AdminListView):
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

# >> LOGIN RESTRICTED VIEWS << #
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

class MyDocuments(AuthListView):
	model = Shareable
	
	def get_queryset(self):
		return Shareable.objects.filter(owner=self.request.user.profile) | Shareable.objects.filter(shared_with=self.request.user.profile)

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
	
def verify_fetch_media(request, filepath):
	file = get_object_or_404(Shareable, doc_file=filepath)
	if request.user.profile in file.shared_with.all() or request.user.profile == file.owner:
		if file.verified:
			return FileResponse(file.doc_file)
		else:
			return HttpResponse("File wasn't verified lol")
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
		form.instance.doc_hash = hashlib.sha256(form.cleaned_data['doc_file'].read()).hexdigest()
		return super().form_valid(form)

def validate_doc(_doc_file):
	# filetype = magic.from_descriptor(_doc_file).lower()
	# accepted_types = ["pdf", "png", "jpeg"]
	# return any(filetype.startswith(x) for x in accepted_types)
	return True

class IssueTicket(View):
	def get(self, request: HttpRequest):
		ctx = {
			'shareables': Shareable.objects.filter(owner=request.user.profile),
			'issued': Profile.objects.get(pk=int(request.GET.get('issued_to')))
		}
		return render(request, template_name="medimode/ticket_form.html", context=ctx)
	
	def post(self, request: HttpRequest):
		#  COLLECT  #
		_issuer = request.user.profile
		_issued = Profile.objects.get(pk=int(request.POST.get("issued_to")))
		_description = request.POST.get("description")
		_otp = request.POST.get("otp")
		
		tkt_shareables = []
		
		#  SANITISE  #
		for _doc_file in request.FILES.getlist("doc_files"):
			if not validate_doc(_doc_file):
				raise ValidationError("Invalid Filetype provided")
		if not verifyOTP(request):
			raise ValidationError("Invalid OTP provided")
		
		#  COMMIT  #
		for _doc_file in request.FILES.getlist("doc_files"):
			tkt_shareable = Ticket_Shareable(doc_file=_doc_file, filename=_doc_file.name, owner=request.user.profile,
																			 party=Ticket_Shareable.PARTY.ISSUER)
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

class MyTicketsforBills(AuthListView):
	template_name = "medimode/previousBills.html"

	def get_queryset(self):
		Temp=Ticket.objects.filter(Q(issuer=self.request.user.profile))
		return [x.issued._meta.object_name == "Doctor" for x in Temp]
		# return Temp

class TicketView(AuthDetailView):
	template_name = "medimode/ticketDetail.html"
	model=Ticket
	
	def post(self, request):
		_money = request.POST.get("money")
		_req = request.POST.get("moneyreq")
		
		if _req and _money:
			payer, paid = (1, 2)

class Search(AuthTemplateView):
	template_name = "medimode/search.html"
	
	def post(self, request):
		category = str_to_model(request.POST.get("category"))
		entity_name = request.POST.get("entity_name")
		
		all_objs = category.objects.all()
		names_obj = {x.full_name: x.user for x in all_objs}
		
		entries_close = set([names_obj[x] for x in difflib.get_close_matches(entity_name, names_obj.keys(), n=10)])
		entries_including = set([names_obj[x] for x in names_obj if entity_name in x])
		
		entries = list(entries_close | entries_including)
		
		return render(request, self.template_name, context={"entries": entries})
