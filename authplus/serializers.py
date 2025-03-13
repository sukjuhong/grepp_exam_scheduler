from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

from customers.serializers import CustomerSerializer


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = None
    access = None
    refreshToken = serializers.CharField(write_only=True)
    accessToken = serializers.CharField(read_only=True)

    class Meta:
        fields = ('refreshToken', 'accessToken')

    def validate(self, attrs):
        attrs = {
            'refresh': attrs.get('refreshToken')
        }
        data = super().validate(attrs)
        return {
            'accessToken': data['access']
        }


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    refreshToken = serializers.CharField(read_only=True)
    accessToken = serializers.CharField(read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        fields = ('refreshToken', 'accessToken', 'customer')

    def validate(self, attrs):
        super().validate(attrs)
        refresh = self.get_token(self.user)
        return {
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
            'customer': CustomerSerializer(self.user).data
        }
