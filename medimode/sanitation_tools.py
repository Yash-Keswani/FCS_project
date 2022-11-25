import bleach
from django.core.exceptions import ValidationError
import magic

from medimode.models import Document, Hospital, Pharmacy, Insurance, Doctor, Patient

def verify_otp(request):
	otp_given = request.POST.get("otp")
	otp_actual = request.user.totp
	if not otp_given == otp_actual:
		raise ValidationError("Invalid OTP provided")

def sanitise_doc(_doc_file):
	filetype = magic.from_buffer(_doc_file.read(256)).lower()
	accepted_types = ["pdf", "png", "jpeg"]
	if not any(filetype.startswith(x) for x in accepted_types):
		raise ValidationError("Invalid file provided")
	return _doc_file

def get_clean(_post, attr):
	value = _post.get(attr)
	if value is None:
		raise ValidationError("Parameters were removed from form")
	else:
		return bleach.clean(value)

def get_clean_int(_post, attr):
	value = _post.get(attr)
	if value is None or not value.isnumeric():
		raise ValidationError("Invalid integer provided")
	return int(value)

def get_clean_or_none(_post, attr):
	value = _post.get(attr)
	if value is not None:
		return bleach.clean(value)
	else:
		return value

def get_document(_files, attr):
	value = _files.get(attr)
	if value is None:
		raise ValidationError("File not found in form")
	else:
		fl = sanitise_doc(_doc_file=value)
		return Document.objects.create(doc_file=fl, filename=fl.name)

def get_document_or_none(_files, attr):
	value = _files.get(attr)
	if value is None:
		return None
	else:
		fl = sanitise_doc(_doc_file=value)
		return Document.objects.create(doc_file=fl, filename=fl.name)
	
model_mapping = {"hospital": Hospital, "pharmacy": Pharmacy, "insurance": Insurance, "doctor": Doctor, "patient": Patient}
def str_to_model(model_name):
	if model_name is None:
		raise ValidationError("Model name not provided")
	mname = model_mapping.get(model_name)
	if mname is None:
		raise ValidationError("Invalid category of profile")
	return mname

def str_to_model_or_none(model_name):
	return model_mapping.get(model_name)
