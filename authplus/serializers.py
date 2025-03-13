from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from customers.serializers import CustomerSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    refreshToken = serializers.CharField(read_only=True)
    accessToken = serializers.CharField(read_only=True)

    class Meta:
        fields = ('refreshToken', 'accessToken')

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data.update({
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token)
        })
        return data


class CustomTokenObtainPairSerializerWithCustomer(TokenObtainPairSerializer):
    refreshToken = serializers.CharField(read_only=True)
    accessToken = serializers.CharField(read_only=True)
    customer = CustomerSerializer(read_only=True)

    class Meta:
        fields = ('refreshToken', 'accessToken', 'customer')

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data.update({
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
            'customer': CustomerSerializer(self.user).data
        })
        return data
