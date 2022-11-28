import os

from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
import stripe
import jwt

from FCS import settings
from medimode.models import Transaction
from mypay.models import Receipt

# stripe.api_key = os.getenv("stripe_api_key")
stripe.api_key = "sk_test_51LzGzTSHQQi3b7Cd6GE6vm8QwZKcpiGw031B5wxuJ8z9dvQ5NGFBxhrBpyi3mmBZ8vBLiPnIjp6htFbg2Dz45dsx00oa5DgphY"


# Create your views here.
class Home(TemplateView):
	template_name = "mypay/index.html"

def transaction_success(request):
	token = request.GET.get("token")
	transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
	t_i = transaction_info
	if (transaction_info["success"] != "1" or
			Receipt.objects.filter(transaction_id=transaction_info["t_id"]).first() is not None):
		return HttpResponseBadRequest()
	else:
		Receipt.objects.create(transaction_id=t_i["t_id"], payer_acct=t_i["payer"], payee_acct=t_i["payee"],
													 status=Receipt.ReceiptStatusChoices.SUCCESS, amount=t_i["price"])
		trn = Transaction.objects.get(id=t_i["t_id"])
		trn.completed = True
		trn.save()
		return redirect(reverse('my_tickets'))

def transaction_failure(request):
	token = request.GET.get("token")
	transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
	if transaction_info["success"] != "-1":
		return HttpResponseBadRequest()
	else:
		return render(request, 'mypay/failure.html')

class MakePayment(View):
	def get(self, request):
		token=request.GET.get("token")
		transaction_info = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
		transaction_info['success'] = "1"
		jwt_success = jwt.encode(transaction_info, settings.SECRET_KEY, algorithm='HS256')
		transaction_info['success'] = "-1"
		jwt_failure = jwt.encode(transaction_info, settings.SECRET_KEY, algorithm='HS256')
		
		if Receipt.objects.filter(transaction_id=transaction_info["t_id"]).first() is not None:
			return HttpResponseBadRequest("Transaction already finished")
		
		product = stripe.Product.create(name="idk payment", stripe_account=transaction_info["payee"])
		price = stripe.Price.create(product=product['id'], unit_amount=str(transaction_info["price"]*100), currency="inr", stripe_account=transaction_info["payee"])
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
			stripe_account=transaction_info["payee"]
		)
	
		return redirect(to=checkout_session.url)
