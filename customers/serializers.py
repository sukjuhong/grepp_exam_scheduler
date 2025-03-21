from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer

from customers.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField()
    last_login = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'


class CustomerChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
