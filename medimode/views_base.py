from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, ListView, CreateView

class ApprovedMixin(UserPassesTestMixin):
	def test_func(self):
		return self.request.user.is_staff or self.request.user.profile.approved
	
class AdminMixin(UserPassesTestMixin):
	def test_func(self):
		return self.request.user.is_staff
	
class AuthTemplateView(LoginRequiredMixin, ApprovedMixin, TemplateView):
	login_url = reverse_lazy('login')
	
class AuthDetailView(LoginRequiredMixin, ApprovedMixin, DetailView):
	login_url = reverse_lazy('login')

class AuthListView(LoginRequiredMixin, ApprovedMixin, ListView):
	login_url = reverse_lazy('login')

class AdminListView(LoginRequiredMixin, AdminMixin, ListView):
	login_url = reverse_lazy('login')
	
class AuthCreateView(LoginRequiredMixin, ApprovedMixin, CreateView):
	login_url = reverse_lazy('login')
