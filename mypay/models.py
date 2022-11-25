from django.db import models
from django.db.models import TextField, BooleanField, TextChoices
from django.forms import CharField

# Create your models here.
class Receipt(models.Model):
	class ReceiptStatusChoices(TextChoices):
		SUCCESS="success"
		PENDING="pending"
		FAILURE="failure"
	
	payer_acct = TextField(max_length=100)
	payee_acct = TextField(max_length=100)
	status = TextField(choices=ReceiptStatusChoices.choices)
