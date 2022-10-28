from django.db import models
from medimode.models import Document, Profile

class Shareable(Document):
	owner = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING, related_name='owned_shareables')
	shared_with = models.ManyToManyField(to=Profile, related_name='can_access')
	
class Transaction(models.Model):
	sender = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING, related_name='sent_transactions')
	receiver = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING, related_name='received_transactions')
	amount = models.SmallIntegerField()
	description = models.TextField(max_length=1024)
	completed = models.BooleanField(default=False)
	
class Ticket_Shareable(Shareable):
	class PARTY(models.TextChoices):
		ISSUER = "Issuer"
		ISSUED = "Issued"
	party = models.TextField(choices=PARTY.choices)

class Ticket(models.Model):
	issuer = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING, related_name='issued_tickets')
	issued = models.ForeignKey(to=Profile, on_delete=models.DO_NOTHING, related_name='accepted_tickets')
	description = models.TextField(max_length=32000)
	shareables = models.ManyToManyField(to=Ticket_Shareable, related_name='owner_ticket')
	transaction = models.OneToOneField(to=Transaction, related_name='ticket', on_delete=models.RESTRICT, null=True)
