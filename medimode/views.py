import hashlib
import os
from django.db.models import Q
import stripe
from django.shortcuts import render, redirect
from django.urls import reverse
from django.urls import reverse_lazy
from medimode.models import Shareable, Profile, Ticket
from medimode.views_base import AuthListView, AuthCreateView, AuthView

# stripe.api_key = os.getenv("stripe_api_key")
stripe.api_key = "sk_test_51LzGzTSHQQi3b7Cd6GE6vm8QwZKcpiGw031B5wxuJ8z9dvQ5NGFBxhrBpyi3mmBZ8vBLiPnIjp6htFbg2Dz45dsx00oa5DgphY"

class Home(AuthView):
	def get(self, request):
		role = self.request.user.is_staff
		if role:
			return redirect(reverse('approve_users'))
		role = self.request.user.role
		if role == "patient":
			return render(request, 'medimode/home.html')
		elif role == "doctor":
			return redirect(reverse('org_home'))
		elif role == "pharmacy":
			return redirect(reverse('org_home'))
		elif role == "hospital":
			return redirect(reverse('org_home'))
		elif role == "insurance":
			return redirect(reverse('org_home'))
		else:
			return render(request, 'medimode/home.html')

class MyTicketsOrg(AuthListView):
	template_name = "medimode/organisationHome.html"
	def get_queryset(self):
		return Ticket.objects.filter(Q(issued=self.request.user.profile) | Q(issuer=self.request.user.profile))

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
		return super().form_valid(form)
