from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .serializers import LoginSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Embed tenant_id in access token
    if user.tenant:
        refresh["tenant_id"] = str(user.tenant.id)
        refresh.access_token["tenant_id"] = str(user.tenant.id)
    refresh["user_id"] = str(user.id)
    refresh.access_token["user_id"] = str(user.id)
    return refresh


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = get_tokens_for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                "access_token": access_token,
                "user": {
                    "email": user.email,
                    "tenant_name": user.tenant.name if user.tenant else None,
                    "role": user.role,
                },
            }
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="Lax",
            secure=not settings.DEBUG,
            max_age=7 * 24 * 60 * 60,
        )
        return response


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token not found."}, status=401)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({"access_token": access_token})
        except (TokenError, InvalidToken) as e:
            return Response({"detail": str(e)}, status=401)
