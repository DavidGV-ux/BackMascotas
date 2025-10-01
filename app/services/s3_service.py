import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-2'))
        self.bucket_name = os.getenv('S3_BUCKET_PHOTOS')
    
    def upload_file(self, file, folder=''):
        """Sube un archivo a S3 y retorna la URL pública"""
        try:
            # Generar nombre único
            filename = secure_filename(file.filename)
            unique_filename = f"{folder}/{uuid.uuid4()}_{filename}"
            
            # Subir archivo
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                unique_filename,
                ExtraArgs={'ContentType': file.content_type}
            )
            
            # Construir URL pública
            url = f"https://{self.bucket_name}.s3.{os.getenv('AWS_REGION', 'us-east-2')}.amazonaws.com/{unique_filename}"
            return url
            
        except ClientError as e:
            print(f"Error uploading file: {e}")
            return None
    
    def delete_file(self, file_url):
        """Elimina un archivo de S3 usando su URL"""
        try:
            # Extraer la key del archivo de la URL
            key = file_url.split('.com/')[-1]
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False
