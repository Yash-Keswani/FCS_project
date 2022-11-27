from django.http import HttpResponseBadRequest, FileResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from medimode.models import Document, Shareable
from medimode.sanitation_tools import str_to_model
from medimode.views_base import AuthView

class ProfileFileView(AuthView):
	def get(self, request, filepath):
		role = request.user.role
		prf=str_to_model(role).objects.get(user=self.request.user)
		
		docs = []
		if role == "doctor":
			docs.extend([prf.proof_of_identity, prf.proof_of_address, prf.medical_license])
		elif role == "patient":
			docs.extend([prf.proof_of_identity, prf.proof_of_address])
			if prf.medical_info is not None:
				docs.append(prf.medical_info)
		else:
			docs.extend([prf.image0, prf.image1])
		
		for doc in docs:
			if filepath == doc.doc_file.name:
				if not doc.verified:
					return HttpResponseBadRequest("The file is not verified")
				return FileResponse(doc.doc_file)
		
		return HttpResponseForbidden("You don't have access to this file")

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
