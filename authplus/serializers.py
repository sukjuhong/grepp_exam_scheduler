from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from customers.serializers import CustomerSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    access = None
    refresh_token = serializers.CharField(write_only=True)
    access_token = serializers.CharField(read_only=True)

    class Meta:
        fields = ('refresh_token', 'access_token')

    def validate(self, attrs):
        attrs = {
            'refresh': attrs.get('refresh_token')
        }
        data = super().validate(attrs)
        return {
            'access_token': data['access']
        }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    refresh_token = serializers.CharField(read_only=True)
    access_token = serializers.CharField(read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        fields = ('refresh_token', 'access_token', 'customer')

    def validate(self, attrs):
        super().validate(attrs)
        refresh = self.get_token(self.user)
        return {
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
            'customer': CustomerSerializer(self.user).data
        }
