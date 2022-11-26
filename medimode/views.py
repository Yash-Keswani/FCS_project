import difflib
import hashlib

from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

from medimode.sanitation_tools import *
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404, FileResponse, HttpResponseForbidden, HttpResponse, JsonResponse
from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth import logout

from medimode.models import Insurance, Hospital, Pharmacy, Doctor, Shareable, Ticket, Profile, Ticket_Shareable, \
	Organisation, User, Patient, Document, Transaction
from medimode.views_base import AuthTemplateView, AuthDetailView, AuthListView, AuthCreateView, AdminListView, AuthView, \
	AdminView

# >> PUBLIC VIEWS << #
@method_decorator(ratelimit(key='post:username', rate='20/m', method='POST', block=True), name='post')
@method_decorator(ratelimit(key='post:username', rate='100/h', method='POST', block=True), name='post')
class Login(LoginView):
	next_page = reverse_lazy("medimode_index")

class Logout(AuthView):
	def get(self,request, **kwargs):
		logout(request)
		return redirect(reverse('login'))
	# next_page = reverse_lazy("medimode_index")

class SignupOrg(TemplateView):
	template_name = "medimode/signup/org.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/signup/org.html',
									{"form": modelform_factory(Organisation, exclude=[]),
									 "state_json": state_text, "state_dict": json.loads(state_text)})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		_username = get_clean(_post, 'username')
		_password= get_clean(_post, 'password')
		_bio= get_clean(_post, 'bio')
		_contact= get_clean_int(_post, 'contact_number')
		
		_image0= sanitise_doc(_files.get('image0'))
		_image1= sanitise_doc(_files.get('image1'))
		
		_location_state= get_clean(_post, 'state')
		_location_city= get_clean(_post, 'city')
		_location= get_clean(_post, 'location')

		tomake = str_to_model(get_clean(_post, "model"))
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password,
																		 role=_post.get('model'))
		_model = tomake.objects.create(bio=_bio, user=_user, contact_number=_contact, image0=_image0, image1=_image1,
																	 location_state=_location_state, location_city=_location_city, location=_location)
		return redirect(reverse('login'))

class SignupIndividual(TemplateView):
	template_name = "medimode/signup/individual.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/signup/individual.html',
									{"form": modelform_factory(Patient, exclude=[])})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		
		#  COLLECTION  #
		_username = get_clean(_post, 'username')
		_password = get_clean(_post, 'password')
		_bio = get_clean(_post, 'bio')
		
		_poa = get_document(_files, 'proof_of_address')
		_poi = get_document(_files, 'proof_of_identity')
		_med_doc = get_document_or_none(_files, 'medical_documents')
		
		#  COMMIT  #
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password, role='patient')
		_model = Patient.objects.create(user=_user, bio=_bio, proof_of_address=_poa,
																		proof_of_identity=_poi, medical_info=_med_doc)
		return redirect(reverse('login'))
	

class SignupDoctor(TemplateView):
	template_name = "medimode/signup/doctor.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/signup/doctor.html',
									{"form": modelform_factory(Doctor, exclude=[])})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		
		#  COLLECTION  #
		_username = get_clean(_post, 'username')
		_password= get_clean(_post, 'password')
		_bio= get_clean(_post, 'bio')
		
		_poa = get_document(_files, 'proof_of_address')
		_poi = get_document(_files, 'proof_of_identity')
		_med_doc= get_document(_files, 'medical_license')
		
		#  COMMIT  #
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password, role='doctor')
		_model = Doctor.objects.create(user=_user, bio=_bio, proof_of_address=_poa,
																		proof_of_identity=_poi, medical_license=_med_doc)
		return redirect(reverse('login'))
	
# >> ADMIN VIEWS << #
class ApproveUsers(AdminListView):
	template_name = "medimode/approve_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=False)
	
	@staticmethod
	def post(request):
		approved_users = request.POST.getlist("approved_users")
		approved_users_updates=[]
		if approved_users is None:
			raise ValidationError()
		for i in approved_users:
			if str(i).isnumeric:
				approved_users_updates.append(i)
			else:
				raise ValidationError("Approved users must be a list of integers")
		approved_profiles = [get_object_or_404(Profile, pk=int(x)) for x in approved_users_updates]
		
		for profile in approved_profiles:
			profile.approved = True
			profile.save()
		
		return redirect(reverse('approve_users'))

class Documents(AdminView):
	@staticmethod
	def post(request):
		_pid = get_clean_int(json.loads(request.body), "profile_id")
		_role = get_object_or_404(Profile, pk=_pid).user.role
		prf = get_object_or_404(str_to_model(_role).objects.select_related('user__profile'), pk=_pid)
		
		docs = []
		if _role == "doctor":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address),
									 ("Medical License", prf.medical_license)])
		elif _role == "patient":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address)])
			if prf.medical_info is not None:
				docs.append(("Medical Info", prf.medical_info))
		else:
			docs = []  # ([("Image 0", prf.image0), ("Image 1", prf.image1)])
		
		tosend = []
		for doc in docs:
			tosend.append({"key": doc[0], "filepath": doc[1].doc_file.name, "filename": doc[1].filename})
		return JsonResponse(tosend, safe=False)

class RemoveUsers(AdminListView):
	template_name = "medimode/reject_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=True)
	
	@staticmethod
	def post(request):
		approved_users = request.POST.get("approved_users")
		approved_users_updates=[]
		if approved_users is None:
			raise ValidationError()
		for i in approved_users:
			if str(i).isnumeric:
				approved_users_updates.append(i)
			else:
				raise ValidationError("Approved users must be a list of integers")
		approved_profiles = [get_object_or_404(Profile,pk=x) for x in approved_users_updates]
		
		for profile in approved_profiles:
			profile.approved = False
			profile.save()
		
		return redirect(reverse('remove_users'))

# >> LOGIN RESTRICTED VIEWS << #
class Home(AuthView):
	def get(self, request):
		role = self.request.user.is_staff
		if role:
			return redirect(reverse('approve_users'))
		role = self.request.user.role
		if role == "patient":
			return render(request, 'medimode/home.html')
		elif role == "doctor":
			return render(request, 'medimode/home.html')
		elif role == "pharmacy":
			return render(request, 'medimode/home.html')
		elif role == "hospital":
			return render(request, 'medimode/home.html')
		elif role == "insurance":
			return render(request, 'medimode/home.html')
		else:
			return render(request, 'medimode/home.html')

class OTPSeed(AuthTemplateView):
	template_name = "medimode/my_seed.html"

class InsuranceView(AuthDetailView):
	model = Insurance

class DoctorView(AuthDetailView):
	model = Doctor

class ProfileView(AuthDetailView):
	model = Profile
	def get_object(self, queryset=None):
		return self.request.user.profile

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
		return Shareable.objects.filter(owner=self.request.user.profile) | Shareable.objects.filter(
			shared_with=self.request.user.profile)

def delete_media(request, filepath):
	file = get_object_or_404(Shareable, doc_file=filepath)
	if request.user.profile == file.owner:
		file.delete()
		return redirect(to=reverse('my_documents'))
	else:
		return HttpResponseForbidden()

def fetch_media(request, filepath):
	if request.user.is_staff:
		return FileResponse(get_object_or_404(Document, doc_file=filepath).doc_file)
	file = get_object_or_404(Shareable, doc_file=filepath)
	if (request.user.profile in file.shared_with.all() or
			request.user.profile == file.owner):
		return FileResponse(file.doc_file)
	else:
		return HttpResponseForbidden()

def verify_fetch_media(request, filepath):
	if request.user.is_staff:
		return FileResponse(get_object_or_404(Document, doc_file=filepath).doc_file)
	file = get_object_or_404(Shareable, doc_file=filepath)
	if (request.user.profile in file.shared_with.all() or
			request.user.profile == file.owner):
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

@method_decorator(ratelimit(key='user', rate='20/m', method='POST', block=True), name='post')
@method_decorator(ratelimit(key='user', rate='100/h', method='POST', block=True), name='post')
class IssueTicket(AuthView):
	@staticmethod
	def get(request: HttpRequest):
		ctx = {
			'shareables': Shareable.objects.filter(owner=request.user.profile),
			'targets': Profile.objects.exclude(user=request.user)
		}
		issued_to = get_clean_or_none(request.GET, 'issued_to')
		if issued_to:
			ctx["issued"] = issued_to
		return render(request, template_name="medimode/ticket_form.html", context=ctx)
	
	def post(self, request: HttpRequest):
		#  COLLECT  #
		_issuer = request.user.profile
		_issued = get_object_or_404(Profile, pk=get_clean_int(request.POST, "issued_to"))
		_description = get_clean(request.POST, "description")
		_otp = get_clean_int(request.POST, "otp")
		
		tkt_shareables = []
		
		#  SANITISE  #
		if request.FILES.getlist("doc_files") is None:
			raise ValidationError("parameter not in form")
		
		cleaned_docs = [sanitise_doc(doc) for doc in request.FILES.getlist("doc_files")]
		verify_otp(request)
		
		#  COMMIT  #
		for _doc_file in cleaned_docs:
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
		tkt = Ticket.objects.create(issuer=_issuer, issued=_issued, description=_description)
		tkt.shareables.add(*tkt_shareables)
		tkt.save()
		
		return redirect(to=reverse('issue_ticket'))

class MyTickets(AuthListView):
	def get_queryset(self):
		return Ticket.objects.filter(Q(issued=self.request.user.profile) | Q(issuer=self.request.user.profile))

class MyTicketsforBills(AuthListView):
	template_name = "medimode/previousBills.html"
	
	def get_queryset(self):
		Temp = Ticket.objects.filter(Q(issuer=self.request.user.profile))
		cat = get_clean(self.request.GET, "issued_to")
		if cat not in ["doctor", "pharmacy", "insurance", "hospital"]:
			return Temp
		else:
			return [x for x in Temp if x.issued.user.role == cat]

class TicketView(AuthDetailView):
	template_name = "medimode/ticketDetail.html"
	model = Ticket
	
	@staticmethod
	def post(request, pk, *args, **kwargs):
		_ticket_id = get_clean_int(request.POST, "ticket_id")
		tkt = get_object_or_404(Ticket, pk=_ticket_id)
		if request.user.profile not in (tkt.issued, tkt.issuer):
			raise ValidationError("Not your Ticket")
		
		if request.POST.get("add_transaction"):
			TicketView.attach_transaction(request, tkt)
		elif request.POST.get("attach_doc"):
			TicketView.attach_document(request, tkt)
		return redirect(reverse('ticket_view', kwargs={"pk":pk}))
	
	@staticmethod
	def attach_transaction(request, tkt):
		_money = get_clean_int(request.POST, "money")
		_req = get_clean(request.POST, "moneyreq")
		
		prf0 = request.user.profile
		prf1 = tkt.issuer if prf0 == tkt.issued else tkt.issued
		
		if _req == "Pay":
			payer, paid = prf0, prf1
		elif _req == "Request":
			payer, paid = prf1, prf0
		else:
			raise ValidationError("Invalid option sent")
		
		trns = Transaction.objects.create(sender=payer, receiver=paid, amount=_money, description="WIP", completed=False)
		tkt.transaction = trns
		tkt.save()
	
	@staticmethod
	def attach_document(request, tkt):
		prf0 = request.user.profile
		prf1 = tkt.issuer if prf0 == tkt.issued else tkt.issued
		
		party = (Ticket_Shareable.PARTY.ISSUER if request.user.profile == tkt.issuer else
						 Ticket_Shareable.PARTY.ISSUED)
		
		if request.FILES.getlist("doc_files") is None:
			raise ValidationError("parameter not in form")
		
		cleaned_docs = [sanitise_doc(doc) for doc in request.FILES.getlist("doc_files")]
		
		shareables = []
		for _doc_file in cleaned_docs:
			tkt_shareable = Ticket_Shareable.objects.create(doc_file=_doc_file, filename=_doc_file.name,
																											owner=request.user.profile, party=party)
			tkt_shareable.shared_with.add(prf1)
			tkt_shareable.save()
			shareables.append(tkt_shareable)
		
		tkt.shareables.add(*shareables)
		tkt.save()
		return render(request, "medimode/ticketDetail.html")
		
with open("medimode/models/cities.json") as _fl:
	state_text = _fl.read()
class Search(AuthTemplateView):
	template_name = "medimode/search.html"
	
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
		
		all_objs = category.objects.filter(Q(location_state=location_state) & Q(location_city=location_city))
		names_obj = {x.full_name: x.user for x in all_objs}
		
		entries_close = set([names_obj[x] for x in difflib.get_close_matches(entity_name, names_obj.keys(), n=10)])
		entries_including = set([names_obj[x] for x in names_obj if entity_name in x])
		
		entries = list(entries_close | entries_including)
		ctx = {"entries": entries, "state_json": state_text, "state_dict": json.loads(state_text)}
		
		return render(request, self.template_name, context=ctx)
