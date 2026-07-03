from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .login import login_with_credentials


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires = serializers.DateTimeField()
    prefix = serializers.CharField()


@method_decorator(csrf_exempt, name="dispatch")
class LoginAPIView(APIView):
    """Exchange username/password for a short-lived Bearer token."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="api_login",
        tags=["auth"],
        request=LoginRequestSerializer,
        responses={200: LoginResponseSerializer},
        auth=[],
    )
    def post(self, request):
        body, status = login_with_credentials(request)
        return Response(body, status=status)


def login_urlpattern():
    from django.urls import path

    return path("login/", LoginAPIView.as_view(), name="login")


