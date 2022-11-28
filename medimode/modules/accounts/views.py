import json
import stripe
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.forms import ValidationError, modelform_factory
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from ratelimit.decorators import ratelimit

from medimode.models import User, Patient, Organisation, Doctor, Profile, Hospital
from medimode.sanitation_tools import get_clean, get_document, get_clean_int, str_to_model, get_document_or_none
from medimode.views_base import AuthView, AuthDetailView, AuthTemplateView

with open("medimode/models/cities.json") as _fl:
	state_text = _fl.read()

@method_decorator(ratelimit(key='post:username', rate='20/m', method='POST', block=True), name='post')
@method_decorator(ratelimit(key='post:username', rate='100/h', method='POST', block=True), name='post')
class Login(LoginView):
	next_page = reverse_lazy("medimode_index")

class Logout(AuthView):
	def get(self, request, **kwargs):
		logout(request)
		return redirect(reverse('login'))

# next_page = reverse_lazy("medimode_index")

class MyStripe(AuthView):
	@staticmethod
	def get(request):
		response = stripe.AccountLink.create(
			account=request.user.stripe_acct,
			return_url=request.build_absolute_uri(reverse('medimode_index')),
			refresh_url=request.build_absolute_uri(reverse('medimode_index')),
			type="account_onboarding",
		)
		return redirect(response["url"])

class SignupOrg(TemplateView):
	template_name = "medimode/_accounts/org.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/_accounts/org.html',
									{"form": modelform_factory(Organisation, exclude=[]),
									 "state_json": state_text, "state_dict": json.loads(state_text)})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		_username = get_clean(_post, 'username')
		_email = get_clean(_post, 'email')
		_password = get_clean(_post, 'password')
		_publicKey = get_clean(_post, 'publicKey')
		# check if public key is hexadecimal
		if not (len(_publicKey) == 42 and _publicKey.startswith('0x')
				and all('9' > ch > '0' or 'F' > ch > 'A' for ch in _publicKey)):
			raise ValidationError("Invalid public key provided")
		
		_bio = get_clean(_post, 'bio')
		_contact = get_clean_int(_post, 'contact_number')
		
		_image0 = get_document(_files, 'image0')
		_image1 = get_document(_files, 'image1')
		
		_location_state = get_clean(_post, 'state')
		_location_city = get_clean(_post, 'city')
		_location = get_clean(_post, 'location')
		
		tomake = str_to_model(get_clean(_post, "model"))
		
		acct = stripe.Account.create(type="custom", business_type="company", capabilities={
			"transfers": {"requested": True},
			"card_payments": {"requested": True},
			"legacy_payments": {"requested": True}}, company={"name": _username})
		_user = User.objects.create_user(username=_username, email=_email, first_name=_username, password=_password,
																		 role=_post.get('model'), stripe_acct=acct["id"], public_key=_publicKey)
		_model = tomake.objects.create(bio=_bio, user=_user, contact_number=_contact, image0=_image0, image1=_image1,
																	 location_state=_location_state, location_city=_location_city, location=_location)
		return redirect(reverse('login'))

class SignupIndividual(TemplateView):
	template_name = "medimode/_accounts/individual.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/_accounts/individual.html',
									{"form": modelform_factory(Patient, exclude=[])})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		
		#  COLLECTION  #
		_username = get_clean(_post, 'username')
		_email = get_clean(_post, 'email')
		_password = get_clean(_post, 'password')
		_bio = get_clean(_post, 'bio')
		_publicKey = get_clean(_post, 'publicKey')
		# check if public key is hexadecimal
		if not (len(_publicKey) == 42 and _publicKey.startswith('0x')
						and all('9' > ch > '0' or 'F' > ch > 'A' for ch in _publicKey)):
			raise ValidationError("Invalid public key provided")
		
		_poa = get_document(_files, 'proof_of_address')
		_poi = get_document(_files, 'proof_of_identity')
		_med_doc = get_document_or_none(_files, 'medical_documents')
		
		acct = stripe.Account.create(type="custom", business_type="company", capabilities={
			"transfers": {"requested": True},
			"card_payments": {"requested": True},
			"legacy_payments": {"requested": True}}, company={"name": _username})
		_user = User.objects.create_user(username=_username, first_name=_username, password=_password, role='patient',
		 																 stripe_acct=acct["id"],public_key=_publicKey)
		_model = Patient.objects.create(user=_user, bio=_bio, proof_of_address=_poa,
																		proof_of_identity=_poi, medical_info=_med_doc)
		return redirect(reverse('login'))

class SignupDoctor(TemplateView):
	template_name = "medimode/_accounts/doctor.html"
	
	@staticmethod
	def get(request, **kwargs):
		return render(request, 'medimode/_accounts/doctor.html',
									{"form": modelform_factory(Doctor, exclude=[]), "hospitals": Hospital.objects.all()})
	
	def post(self, request):
		_post = self.request.POST
		_files = self.request.FILES
		
		#  COLLECTION  #
		_username = get_clean(_post, 'username')
		_email = get_clean(_post, 'email')
		_password = get_clean(_post, 'password')
		_bio = get_clean(_post, 'bio')
		_publicKey = get_clean(_post, 'publicKey')
		_works_at = _post.get('works_at')
		if not _works_at:
			_works_at = None
		else:
			_works_at = get_clean_int(_post, 'works_at')
		# check if public key is hexadecimal
		if not (len(_publicKey) == 42 and _publicKey.startswith('0x')
						and all('9' > ch > '0' or 'F' > ch > 'A' for ch in _publicKey)):
			raise ValidationError("Invalid public key provided")
		
		_poa = get_document(_files, 'proof_of_address')
		_poi = get_document(_files, 'proof_of_identity')
		_med_doc = get_document(_files, 'medical_license')
		
		acct = stripe.Account.create(type="custom", business_type="company", capabilities={
			"transfers": {"requested": True},
			"card_payments": {"requested": True},
			"legacy_payments": {"requested": True}}, company={"name": _username})
		_user = User.objects.create_user(username=_username, email=_email, first_name=_username, password=_password,
																		 role='doctor', stripe_acct=acct["id"], public_key=_publicKey)
		_model = Doctor.objects.create(user=_user, bio=_bio, proof_of_address=_poa,
																	 proof_of_identity=_poi, medical_license=_med_doc, works_at=_works_at)
		return redirect(reverse('login'))

class ProfileView(AuthDetailView):
	template_name = "medimode/_accounts/profile_detail.html"
	model = Profile
	
	def get_object(self, queryset=None):
		return self.request.user.profile
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data()
		context['role'] = self.request.user.role
		
		role = self.request.user.role
		prf = str_to_model(role).objects.get(user=self.request.user)
		# get context data
		
		docs = []
		if role == "doctor":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address),
									 ("Medical License", prf.medical_license)])
		elif role == "patient":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address)])
			if prf.medical_info is not None:
				docs.append(("Medical Info", prf.medical_info))
		else:
			docs = ([("Image 0", prf.image0), ("Image 1", prf.image1)])
		context['docs'] = docs
		return context

class OTPSeed(AuthTemplateView):
	template_name = "medimode/_accounts/my_seed.html"

class EditProfile(AuthTemplateView):
	template_name = "medimode/_accounts/edit_profile.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data()
		user = self.request.user
		role = user.role
		prf = str_to_model(role).objects.get(user=user)
		context['prf'] = prf
		
		docs = []
		if role == "doctor":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address),
									 ("Medical License", prf.medical_license)])
		elif role == "patient":
			docs.extend([("Proof of Identity", prf.proof_of_identity),
									 ("Proof of Address", prf.proof_of_address)])
			if prf.medical_info is not None:
				docs.append(("Medical Info", prf.medical_info))
		else:
			docs = ([("Image 0", prf.image0), ("Image 1", prf.image1)])
		context['docs'] = docs
		
		return context
	
	def post(self, request, **kwargs):
		_post = self.request.POST
		_files = self.request.FILES
		user = request.user
		role = user.role
		prf = str_to_model(role).objects.get(user=user)
		_password = _post.get('password')
		if not _password:
			_password = user.password
		else:
			_password = get_clean(_post, 'password')
			user.set_password(_password)
		
		_email = _post.get('email')
		if not _email:
			_email = user.email
		else:
			_email = get_clean(_post, 'email')
			user.email = _email
		
		_bio = _post.get('bio')
		if not _bio:
			_bio = prf.bio
		if not _bio:
			_bio = prf.bio
		else:
			_bio = get_clean(_post, 'bio')
		prf.bio = _bio
		
		_poa, _poi = None, None
		if role == "doctor":
			_poa = get_document_or_none(_files, 'proof_of_address')
			_poi = get_document_or_none(_files, 'proof_of_identity')
			_med_doc = get_document_or_none(_files, 'medical_license')
			if _med_doc is None:
				_med_doc = prf.medical_license
			prf.medical_license = _med_doc
		if role == "patient":
			_poa = get_document_or_none(_files, 'proof_of_address')
			_poi = get_document_or_none(_files, 'proof_of_identity')
			_med_doc = get_document_or_none(_files, 'medical_info')
			if _med_doc is None:
				_med_doc = prf.medical_info
			prf.medical_info = _med_doc
		
		if _poa is None:
			_poa = prf.proof_of_address
		if _poi is None:
			_poi = prf.proof_of_identity
		prf.proof_of_address = _poa
		prf.proof_of_identity = _poi
		prf.save()
		user.save()
		
		return redirect(reverse('medimode_index'))

@method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True), name='get')
@method_decorator(ratelimit(key='ip', rate='50/h', method='POST', block=True), name='get')
class SendOTP(AuthView):
	def get(self, request):  # TODO: change to post
		user = request.user
		send_mail(
			'Your OTP | Medimode Solutions',
			f"Here's your OTP: {user.totp}",
			'test.com',
			[user.email]
		)
