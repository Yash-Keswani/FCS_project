from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .doc_models import Document

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='%(class)s')
	bio = models.TextField(max_length=500, blank=True)

	@property
	def full_name(self):
		return self.user.first_name + " " + self.user.last_name
	
	class Meta:
		abstract = True

class Individual(Profile):
	def delete(self, using=None, keep_parents=False):
		super().delete()
		self.proof_of_identity.delete()
		self.proof_of_address.delete()
		
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
	image0 = models.ImageField(upload_to='uploads/images/')  # upload with appropriate name?
	image1 = models.ImageField(upload_to='uploads/images/')
	location = models.TextField(max_length=200)  # this is lazy but I couldn't care less
	
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
