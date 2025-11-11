"""
import functools
from datetime import datetime, timezone
import jwt
import rest_framework
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request

from main.models import ShopUser


def token_validation_required(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):

        for i in range(len(args)):
            if type(args[i]) is rest_framework.request.Request:
                break
        request = args[i]
        if request.META.get('HTTP_AUTHORIZATION') is not None:
            token = request.META['HTTP_AUTHORIZATION']
            user = token_auth(token)

            if user is not None:
                kwargs['user'] = user
                return func(*args, **kwargs)

        return Response({"Invalid token": request.data}, status=status.HTTP_400_BAD_REQUEST)

    return wrapper

def token_auth(encoded_jwt):
    try:
        decoded_jwt = jwt.decode(encoded_jwt, settings.SECRET_KEY, algorithms=['HS256'])
        user = ShopUser.objects.get(id = decoded_jwt['user_id']) # -> email
        # user_id = decoded_jwt['user_id']
        if decoded_jwt['exp'] >= int(datetime.now().timestamp()):
            return user
    except:
        return None

    # except Exception as e:
    #     print(f"Ошибка: {type(e).__name__}: {e}")  # Общий catch
    #     return None
"""