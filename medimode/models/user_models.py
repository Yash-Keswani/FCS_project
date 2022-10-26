from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='%(class)s')
	bio = models.TextField(max_length=500, blank=True)

	@property
	def full_name(self):
		return self.user.first_name + " " + self.user.last_name

	class Meta:
		abstract = True
		
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
	instance.profile.save()


class Document(models.Model):
	# MIGHT become a field instead of a model
	# Delete document when class using the document is deleted
	# Document validation can be performed
	doc_file = models.FileField(upload_to='uploads/documents')
	filename = models.CharField(max_length=100)

class Individual(Profile):
	proof_of_identity = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="poi_%(class)s")
	proof_of_address = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="poa_%(class)s")
	
	class Meta:
		abstract = True

class Doctor(Individual):
	medical_license = models.OneToOneField(Document, on_delete=models.RESTRICT, related_name="owner_doctor")
	
class Patient(Individual):
	medical_info = models.OneToOneField(Document, on_delete=models.SET_NULL, related_name="owner_patient", null=True)

class Organisation(Profile):
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

class Insurance(Organisation):
	pass
	