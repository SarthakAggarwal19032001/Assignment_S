from django.db import models

class ImageProcessingRequest(models.Model):
    request_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)

class Product(models.Model):
    name = models.CharField(max_length=255)

class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    input_url = models.URLField()
    output_url = models.URLField(null=True, blank=True)
    request = models.ForeignKey(ImageProcessingRequest, on_delete=models.CASCADE)
