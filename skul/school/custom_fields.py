from django.db import models
from cloudinary.models import CloudinaryField as BaseCloudinaryField

class CloudinaryField(BaseCloudinaryField):
    def __init__(self, *args, **kwargs):
        from cloudinary import config as cloudinary_config
        cloudinary_config()  
        super().__init__(*args, **kwargs)