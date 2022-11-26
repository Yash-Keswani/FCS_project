import base64
import secrets

import mintotp as mintotp
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import TextChoices
from django_cryptography.fields import encrypt

from .doc_models import Document

def gen_otpseed():
	return base64.b32encode(secrets.token_bytes(10)).decode(encoding='utf-8')

class User(AbstractUser):
	class UserRoleChoices(TextChoices):
		PATIENT = "patient"
		DOCTOR = "doctor"
		HOSPITAL = "hospital"
		PHARMACY = "pharmacy"
		INSURANCE = "insurance"
	
	@property
	def totp(self):
		return mintotp.totp(self.OTP_seed)
	
	role = models.TextField(choices=UserRoleChoices.choices, null=True)
	OTP_seed = encrypt(models.TextField(default=gen_otpseed))
	stripe_acct = models.TextField(max_length=100, blank=True)
	
	@property
	def profile(self):
		urc = self.UserRoleChoices
		mapping = {urc.DOCTOR: self.doctor, urc.PATIENT: self.patient, urc.HOSPITAL: self.hospital,
							 urc.PHARMACY: self.pharmacy, urc.INSURANCE: self.insurance}
		return mapping.get(self.role)

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='%(class)s')
	bio = models.TextField(max_length=500, blank=True)
	approved = models.BooleanField(default=False)
	
	@property
	def full_name(self):
		return self.user.first_name + " " + self.user.last_name
	
	def __str__(self):
		return self.full_name

class Individual(Profile):
	def delete(self, using=None, keep_parents=False):
		super().delete()
		self.proof_of_identity.delete()
		self.proof_of_address.delete()
		# TODO: delete shareable documents uploaded by user,
	
	proof_of_identity = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="poi_%(class)s")
	proof_of_address = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="poa_%(class)s")
	
	class Meta:
		abstract = True

class Doctor(Individual):
	def delete(self, using=None, keep_parents=False):
		super().delete()
		self.medical_license.delete()
	
	medical_license = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="owner_doctor")

class Patient(Individual):
	def delete(self, using=None, keep_parents=False):
		super().delete()
		self.medical_info.delete()
	
	medical_info = models.OneToOneField(Document, on_delete=models.SET_NULL, related_name="owner_patient", null=True)

class Organisation(Profile):
	def delete(self, using=None, keep_parents=False):
		super().delete()
		self.image0.delete()
		self.image1.delete()
	
	contact_number = models.BigIntegerField(validators=[MinValueValidator(1000_0000), MaxValueValidator(99_9999_9999)])
	# could be another model for image info with many-to-one relation
	image0 = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="img0_%(class)s")
	image1 = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="img1_%(class)s")
	location_state = models.TextField(max_length=200, default="Delhi")
	location_city = models.TextField(max_length=200, default="New Delhi")
	location = models.TextField(max_length=200)
	
	class Meta:
		abstract = True

class Hospital(Organisation):
	pass

class Pharmacy(Organisation):
	pass
	
	class Meta:
		verbose_name_plural = "Pharmacies"

class Insurance(Organisation):
	pass
	
	class Meta:
		verbose_name_plural = "Insurance Firms"
