from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, ListView, CreateView

class AuthTemplateView(LoginRequiredMixin, TemplateView):
	login_url = reverse_lazy('login')
	
class AuthDetailView(LoginRequiredMixin, DetailView):
	login_url = reverse_lazy('login')

class AuthListView(LoginRequiredMixin, ListView):
	login_url = reverse_lazy('login')
	
class AuthCreateView(LoginRequiredMixin, CreateView):
	login_url = reverse_lazy('login')
