from django.db import models

class Document(models.Model):
	def delete(self, using=None, keep_parents=False):
		self.doc_file.delete()
		super().delete()
	# MIGHT become a field instead of a model
	# Delete document when class using the document is deleted
	# Document validation can be performed
	doc_file = models.FileField(upload_to='uploads/documents')
	filename = models.CharField(max_length=100)
