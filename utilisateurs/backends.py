from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        userModel = get_user_model()
        try:
            user = userModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except userModel.DoesNotExist:
            return None