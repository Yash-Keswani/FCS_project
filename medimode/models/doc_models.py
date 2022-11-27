from django.db import models
from hashlib import sha256

def check_blockchain(d_hash):
	return True

def ask_blockchain(d_hash):
	return "0x00"

class Document(models.Model):
	def delete(self, using=None, keep_parents=False):
		self.doc_file.delete()
		super().delete()
		
	@property
	def verified(self):
		return check_blockchain(self.doc_hash)
	
	# might become a field instead of a model
	# Delete document when class using the document is deleted
	# Document validation can be performed
	doc_file = models.FileField(upload_to='uploads/documents')
	doc_hash = models.CharField(max_length=256, default='')
	filename = models.CharField(max_length=100)

	def __str__(self):
		return self.filename
