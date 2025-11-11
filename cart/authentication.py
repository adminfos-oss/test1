# cart\authentication.py
"""
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from main.authenticate import token_auth  # JWT-декодер
class JWTAuthenticationFromHeader(BaseAuthentication):

    def authenticate(self, request):
        token_encoded_jwt = request.META.get('HTTP_AUTHORIZATION')
        if not token_encoded_jwt:
            return None  # аноним разрешён
        try:
            shop_user = token_auth(token_encoded_jwt)
            if shop_user and shop_user.is_active:
                return shop_user, None
        except Exception:
            raise AuthenticationFailed('Invalid token')
        return None
"""