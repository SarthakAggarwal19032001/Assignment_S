from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .models import ImageProcessingRequest, Product, Image
import uuid
import pandas as pd
import csv

class UploadCSV(APIView):
    parser_classes = (MultiPartParser, FormParser)  # Ensure file is handled properly

    def post(self, request):
        file = request.FILES.get("file")  # Get the uploaded file
        df = pd.read_csv(file, encoding="utf-16")
        df.to_csv("your_file_utf8.csv", index=False, encoding="utf-8")
        if file is None:
            return Response({"error": "No file uploaded"}, status=400)

        if not file.name.endswith(".csv"):
            return Response({"error": "Invalid file format. Please upload a CSV file."}, status=400)

        request_id = str(uuid.uuid4())
        processing_request = ImageProcessingRequest.objects.create(request_id=request_id, status="pending")

        try:
            csv_data = file.read().decode("utf-8").splitlines()
            reader = csv.reader(csv_data)
            next(reader)  # Skip header row

            with transaction.atomic():
                for row in reader:
                    if len(row) < 3:
                        return Response({"error": "Invalid CSV format. Missing columns."}, status=400)

                    product_name = row[1]
                    input_urls = row[2].split(",")

                    product, _ = Product.objects.get_or_create(name=product_name)
                    for img_url in input_urls:
                        Image.objects.create(product=product, input_url=img_url.strip(), request=processing_request)

        except Exception as e:
            return Response({"error": f"Error processing CSV: {str(e)}"}, status=500)

        # Trigger Celery task
        from .tasks import process_images
        process_images.delay(request_id)

        return Response({"request_id": request_id})



class CheckStatus(APIView):
    def get(self, request, request_id):
        try:
            processing_request = ImageProcessingRequest.objects.get(request_id=request_id)
            images = Image.objects.filter(request=processing_request)
            output_urls = [img.output_url for img in images if img.output_url]

            return Response({
                "status": processing_request.status,
                "output_urls": output_urls
            })
        except ImageProcessingRequest.DoesNotExist:
            return Response({"error": "Invalid request ID"}, status=404)

