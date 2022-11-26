from django.db import models
from django.db.models import TextField, BooleanField, TextChoices, IntegerField

# Create your models here.
class Receipt(models.Model):
	class ReceiptStatusChoices(TextChoices):
		SUCCESS="success"
		PENDING="pending"
		FAILURE="failure"
	
	transaction_id = IntegerField()
	payer_acct = TextField(max_length=100)
	payee_acct = TextField(max_length=100)
	amount = IntegerField()
	status = TextField(choices=ReceiptStatusChoices.choices)
