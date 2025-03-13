from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
        }


class CustomerTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        super().validate(attrs)
        refresh = self.get_token(self.user)
        return {
            'refreshToken': str(refresh),
            'accessToken': str(refresh.access_token),
            'customer': CustomerSerializer(self.user).data
        }
