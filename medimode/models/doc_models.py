from django.db import models
from hashlib import sha256

class Document(models.Model):
	def delete(self, using=None, keep_parents=False):
		self.doc_file.delete()
		super().delete()
		
	@property
	def verified(self):
		with open(self.doc_file.path, mode='rb') as fd:
			return sha256(fd.read()).hexdigest() == self.doc_hash
		# TODO: use blockchain here
	
	# might become a field instead of a model
	# Delete document when class using the document is deleted
	# Document validation can be performed
	doc_file = models.FileField(upload_to='uploads/documents')
	doc_hash = models.CharField(max_length=256, default='')
	filename = models.CharField(max_length=100)

	def __str__(self):
		return self.filename
