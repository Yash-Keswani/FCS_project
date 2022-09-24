from django.http import HttpRequest
from django.shortcuts import render

def home(req: HttpRequest):
	return render(req, "home.html")
	