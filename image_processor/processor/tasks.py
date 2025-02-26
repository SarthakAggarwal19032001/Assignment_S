from celery import shared_task
from .models import ImageProcessingRequest, Image
import requests
from PIL import Image as PILImage
from io import BytesIO
import boto3  # For S3 storage (optional)

@shared_task
def process_images(request_id):
    processing_request = ImageProcessingRequest.objects.get(request_id=request_id)
    processing_request.status = "processing"
    processing_request.save()

    images = Image.objects.filter(request=processing_request)
    for img in images:
        response = requests.get(img.input_url)
        img_obj = PILImage.open(BytesIO(response.content))
        img_obj = img_obj.convert("RGB")
        img_obj.save(f"{img.id}.jpg", "JPEG", quality=50)

        # Upload to S3 or save locally
        output_url = f"http://localhost:8000/media/{img.id}.jpg"
        img.output_url = output_url
        img.save()

    processing_request.status = "completed"
    processing_request.save()
