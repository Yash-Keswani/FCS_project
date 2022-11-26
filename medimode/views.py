import hashlib
import os

import stripe
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy

from medimode.models import Shareable, Profile
from medimode.views_base import AuthListView, AuthCreateView, AuthView

stripe.api_key = os.getenv("stripe_api_key")

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

class MyDocuments(AuthListView):
	model = Shareable
	
	def get_queryset(self):
		return Shareable.objects.filter(owner=self.request.user.profile) | Shareable.objects.filter(
			shared_with=self.request.user.profile)

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
