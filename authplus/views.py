from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema


from .serializers import CustomTokenRefreshSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        summary="로그인",
        description="회사명과 비밀번호로 로그인합니다. 로그인 성공 시 엑세스 토큰과 리프레쉬 토큰, 고객 정보를 반환합니다.",
        responses={200: CustomTokenObtainPairSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    @extend_schema(
        summary="토큰 갱신",
        description="리프레쉬 토큰을 사용하여 엑세스 토큰을 갱신합니다. 갱신 성공 시 두 토큰을 반환합니다.",
        responses={200: CustomTokenRefreshSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
