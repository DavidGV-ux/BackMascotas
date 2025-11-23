import os
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid
import mimetypes


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'us-east-2'))
        # Usar el bucket especificado o el valor por defecto
        self.bucket_name = os.getenv('S3_BUCKET_PHOTOS', 'imagenesmascotasalec')
    
    def upload_file(self, file, folder=''):
        """Sube un archivo a S3 y retorna la URL pública"""
        try:
            if not self.bucket_name:
                print("Error: S3_BUCKET_PHOTOS no está configurado")
                return None
            
            # Asegurarse de que el archivo esté al inicio
            if hasattr(file, 'seek'):
                file.seek(0)
            
            # Generar nombre único
            filename = secure_filename(file.filename) if file.filename else 'imagen'
            unique_filename = f"{folder}/{uuid.uuid4()}_{filename}" if folder else f"{uuid.uuid4()}_{filename}"
            
            # Detectar ContentType
            content_type = None
            if hasattr(file, 'content_type') and file.content_type:
                content_type = file.content_type
            else:
                # Intentar detectar desde la extensión del archivo
                content_type, _ = mimetypes.guess_type(filename)
            
            # Si no se puede detectar, usar un tipo por defecto basado en la extensión
            if not content_type:
                ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
                content_type_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'webp': 'image/webp'
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
            
            # Preparar argumentos extra
            # No usar ACL ya que el bucket no permite ACLs
            # El bucket debe tener una política de bucket que permita acceso público
            extra_args = {
                'ContentType': content_type
            }
            
            # Subir archivo
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                unique_filename,
                ExtraArgs=extra_args
            )
            
            # Construir URL pública
            region = os.getenv('AWS_REGION', 'us-east-2')
            url = f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
            return url
            
        except ClientError as e:
            print(f"Error uploading file to S3: {e}")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"Error inesperado al subir archivo: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_file(self, file_url):
        """Elimina un archivo de S3 usando su URL"""
        try:
            if not self.bucket_name:
                print("Error: S3_BUCKET_PHOTOS no está configurado")
                return False
            
            if not file_url:
                return False
            
            # Extraer la key del archivo de la URL
            # Puede venir en formato: https://bucket.s3.region.amazonaws.com/key
            if '.com/' in file_url:
                key = file_url.split('.com/')[-1]
            elif '.amazonaws.com/' in file_url:
                key = file_url.split('.amazonaws.com/')[-1]
            else:
                # Si no tiene formato de URL, asumir que es la key directamente
                key = file_url
            
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
            
        except ClientError as e:
            print(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            print(f"Error inesperado al eliminar archivo: {e}")
            return False
