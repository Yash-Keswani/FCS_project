from django.http import HttpRequest
from django.shortcuts import render
from django.views.generic import TemplateView, DetailView

from medimode.models import Insurance

class Home(TemplateView):
	template_name = "medimode/home.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

class InsuranceView(DetailView):
	model = Insurance
	