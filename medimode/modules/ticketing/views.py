import jwt
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

from FCS import settings
from medimode.models import Ticket, Transaction, Ticket_Shareable, Profile, Shareable
from medimode.sanitation_tools import get_clean, get_clean_int, sanitise_doc, get_clean_or_none, verify_otp
from medimode.views_base import AuthListView, AuthDetailView, AuthView

class MyTickets(AuthListView):
	template_name = "medimode/ticketing/ticket_list.html"
	def get_queryset(self):
		return Ticket.objects.filter(Q(issued=self.request.user.profile) | Q(issuer=self.request.user.profile))

class MyTicketsforBills(AuthListView):
	template_name = "medimode/ticketing/previousBills.html"
	
	def get_queryset(self):
		Temp = Ticket.objects.filter(Q(issuer=self.request.user.profile))
		cat = get_clean(self.request.GET, "issued_to")
		if cat not in ["doctor", "pharmacy", "insurance", "hospital"]:
			return Temp
		else:
			return [x for x in Temp if x.issued.user.role == cat]

class VerifyTicketDocument(AuthView):
	"""This is necessary before recipient can attach documents to ticket or transaction can be created"""
	
	def post(self, request):
		ticket_id = get_clean_int(request.POST, "ticket_id")
		doc_id = get_clean_int(request.POST, "ticket_id")
		target = get_object_or_404(Ticket, pk=ticket_id)
		document = get_object_or_404(Shareable, pk=doc_id)
		pass

def verify_document(ticket, document: Shareable):
	target_role = ticket.issued.user.role
	if target_role == 'pharmacy':
		return document.get_owner_from_blockchain().role == 'doctor'
	elif target_role == 'hospital':
		return document.get_owner_from_blockchain().role == 'doctor'
	elif target_role == 'insurance':
		return document.get_owner_from_blockchain().role == 'hospital'
	return True

def verify_ticket(ticket):
	return any(verify_document(ticket, x) for x in ticket.shareables.all())
	
class TicketView(AuthDetailView):
	template_name = "medimode/ticketing/ticketDetail.html"
	model = Ticket
	
	def get_object(self, queryset=None):
		tkt = super().get_object()
		if self.request.user.profile not in (tkt.issued, tkt.issuer):
			raise ValidationError("Not your Ticket")
		return tkt
		
	@staticmethod
	def post(request, pk, *args, **kwargs):
		_ticket_id = get_clean_int(request.POST, "ticket_id")
		tkt = get_object_or_404(Ticket, pk=_ticket_id)
		if request.user.profile not in (tkt.issued, tkt.issuer):
			raise ValidationError("Not your Ticket")
		if not verify_ticket(tkt):
			raise ValidationError("This ticket isn't verified")
		
		if request.POST.get("add_transaction") and request.user.role != "patient":
			TicketView.attach_transaction(request, tkt)
		elif request.POST.get("attach_doc"):
			TicketView.attach_document(request, tkt)
		elif request.POST.get("pay") and tkt.transaction:
			return redirect(reverse('pay', kwargs={"pk": tkt.transaction_id}))
		return redirect(reverse('ticket_view', kwargs={"pk": pk}))
	
	@staticmethod
	def attach_transaction(request, tkt):
		_money = get_clean_int(request.POST, "money")
		_req = get_clean(request.POST, "moneyreq")
		
		prf0 = request.user.profile
		prf1 = tkt.issuer if prf0 == tkt.issued else tkt.issued
		
		if _req == "Pay":
			payer, paid = prf0, prf1
		elif _req == "Request":
			payer, paid = prf1, prf0
		else:
			raise ValidationError("Invalid option sent")
		
		trns = Transaction.objects.create(sender=payer, receiver=paid, amount=_money, description="WIP", completed=False)
		tkt.transaction = trns
		tkt.save()
	
	@staticmethod
	def attach_document(request, tkt):
		prf0 = request.user.profile
		prf1 = tkt.issuer if prf0 == tkt.issued else tkt.issued
		
		party = (Ticket_Shareable.PARTY.ISSUER if request.user.profile == tkt.issuer else
						 Ticket_Shareable.PARTY.ISSUED)
		
		if request.FILES.getlist("doc_files") is None:
			raise ValidationError("parameter not in form")
		
		cleaned_docs = [sanitise_doc(doc) for doc in request.FILES.getlist("doc_files")]
		
		shareables = []
		for _doc_file in cleaned_docs:
			tkt_shareable = Ticket_Shareable.objects.create(doc_file=_doc_file, filename=_doc_file.name,
																											owner=request.user.profile, party=party)
			tkt_shareable.shared_with.add(prf1)
			tkt_shareable.save()
			shareables.append(tkt_shareable)
		
		tkt.shareables.add(*shareables)
		tkt.save()
		return render(request, "medimode/ticketing/ticketDetail.html")

@method_decorator(ratelimit(key='user', rate='20/m', method='POST', block=True), name='post')
@method_decorator(ratelimit(key='user', rate='100/h', method='POST', block=True), name='post')
class IssueTicket(AuthView):
	@staticmethod
	def get(request: HttpRequest):
		q = Shareable.objects.filter(Q(shared_with=request.user.profile) | Q(owner=request.user.profile))
		ctx = {
			'shareables': q,
			'targets': Profile.objects.exclude(user=request.user)
		}
		issued_to = get_clean_or_none(request.GET, 'issued_to')
		if issued_to:
			ctx["issued"] = issued_to
		return render(request, template_name="medimode/ticketing/ticket_form.html", context=ctx)
	
	def post(self, request: HttpRequest):
		#  COLLECT  #
		_issuer = request.user.profile
		_issued = get_object_or_404(Profile, pk=get_clean_int(request.POST, "issued_to"))
		_description = get_clean(request.POST, "description")
		_otp = get_clean_int(request.POST, "otp")
		
		tkt_shareables = []
		
		#  SANITISE  #
		if request.FILES.getlist("doc_files") is None:
			raise ValidationError("parameter not in form")
		
		cleaned_docs = [sanitise_doc(doc) for doc in request.FILES.getlist("doc_files")]
		verify_otp(request)
		
		#  COMMIT  #
		for _doc_file in cleaned_docs:
			tkt_shareable = Ticket_Shareable(doc_file=_doc_file, filename=_doc_file.name, owner=request.user.profile,
																			 party=Ticket_Shareable.PARTY.ISSUER)
			tkt_shareable.save()
			tkt_shareable.shared_with.add(_issued)
			tkt_shareable.save()
			tkt_shareables.append(tkt_shareable)
			
		if request.POST.get("shareables"):
			_shareables = [get_object_or_404(Shareable, pk=x) for x in request.POST.getlist("shareables")]
			# TODO: only allow user to attach shareables that they have access to. dont attach same shareable twice
			for shareable in _shareables:
				tkt_shareable = Ticket_Shareable(shareable_ptr_id=shareable.id, id=shareable.id)
				tkt_shareable.party = Ticket_Shareable.PARTY.ISSUER
				tkt_shareable.save_base(raw=True)
				tkt_shareable.shared_with.add(_issued)
				tkt_shareable.save_base(raw=True)
				tkt_shareables.append(tkt_shareable)
			
		tkt = Ticket.objects.create(issuer=_issuer, issued=_issued, description=_description)
		tkt.shareables.add(*tkt_shareables)
		tkt.save()
		
		return redirect(to=reverse('my_tickets'))


class MakePayment(AuthView):
	def get(self, request, pk):
		trns = get_object_or_404(Transaction, pk=pk)
		if trns.completed:
			return HttpResponseBadRequest("Transaction is already completed")
		transaction_info = {
			"t_id": trns.id,
			"payer": trns.sender.user.stripe_acct,
			"payee": trns.receiver.user.stripe_acct,
			"price": trns.amount,
			"success": 0
		}
		my_jwt = jwt.encode(transaction_info, settings.SECRET_KEY, algorithm='HS256')
		return redirect(reverse('make_payment')+"?token="+my_jwt)
