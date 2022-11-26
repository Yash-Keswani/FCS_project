import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from medimode.models import Profile
from medimode.sanitation_tools import sanitise_numeric, get_clean_int, str_to_model
from medimode.views_base import AdminListView, AdminView

class ApproveUsers(AdminListView):
	template_name = "medimode/admin/approve_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=False)
	
	@staticmethod
	def post(request):
		approved_users = request.POST.getlist("approved_users")
		if approved_users is None:
			raise ValidationError("Parameter missing")
		approved_users = [sanitise_numeric(x) for x in approved_users]
		approved_profiles = [get_object_or_404(Profile, pk=x) for x in approved_users]
		
		for profile in approved_profiles:
			profile.approved = True
			profile.save()
		
		return redirect(reverse('approve_users'))

class RemoveUsers(AdminListView):
	template_name = "medimode/admin/reject_users.html"
	model = Profile
	
	def get_queryset(self):
		return Profile.objects.filter(approved=True)
	
	@staticmethod
	def post(request):
		approved_users = request.POST.getlist("approved_users")
		if approved_users is None:
			raise ValidationError("Parameter missing")
		approved_users = [sanitise_numeric(x) for x in approved_users]
		approved_profiles = [get_object_or_404(Profile, pk=x) for x in approved_users]
		
		for profile in approved_profiles:
			profile.approved = False
			profile.save()
		
		return redirect(reverse('remove_users'))

class Documents(AdminView):
	@staticmethod
	def post(request):
		_pid = get_clean_int(json.loads(request.body), "profile_id")
		_role = get_object_or_404(Profile, pk=_pid).user.role
		prf = get_object_or_404(str_to_model(_role).objects.select_related('user__profile'), pk=_pid)
		
		docs = []
		tosend = []
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
			docs.extend([("Image 0", prf.image0), ("Image 1", prf.image1)])
		
		for doc in docs:
			tosend.append({"key": doc[0], "filepath": doc[1].doc_file.name, "filename": doc[1].filename})
		return JsonResponse(tosend, safe=False)
