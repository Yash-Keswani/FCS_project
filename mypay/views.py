from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
import stripe
import jwt

from FCS import settings

stripe.api_key = 'sk_test_tR3PYbcVNZZ796tH88S4VQ2u'

# Create your views here.
class Home(TemplateView):
	template_name = "mypay/index.html"
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context["test"] = "This value is useless"
		return context

def transaction_success(request, token: str):
	transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
	if transaction_info["status"] != 1:
		return HttpResponseBadRequest()
	else:
		return render(request, reverse('success'))

def transaction_failure(request, token: str):
	transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
	if transaction_info["status"] != -1:
		return HttpResponseBadRequest()
	else:
		return render(request, reverse('failure'))

class MakePayment(View):
	def get(self, request):
		token = request.GET.get("token")
		transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
		transaction_info['success'] = "1"
		jwt_success = jwt.encode(transaction_info, settings.SECRET_KEY, algorithm='HS256')
		transaction_info['success'] = "-1"
		jwt_failure = jwt.encode(transaction_info, settings.SECRET_KEY, algorithm='HS256')
		
		product = stripe.Product.create(name="idk payment")
		price = stripe.Price.create(product=product['id'], unit_amount=transaction_info["price"], currency="inr")
		checkout_session = stripe.checkout.Session.create(
			line_items=[
				{
					'price': price['id'],
					'quantity': 1
				},
			],
			mode='payment',
			success_url=request.build_absolute_uri(reverse('success') + "?token=" + jwt_success),
			cancel_url=request.build_absolute_uri(reverse('failure') + "?token=" + jwt_failure),
		)
	
		print(checkout_session.url)
		return redirect(to=checkout_session.url)
