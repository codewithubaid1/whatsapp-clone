from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    profile_name = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to='Profile_pics', blank=True, null=True, default='default.png')
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"{self.user.username}'s Profile"