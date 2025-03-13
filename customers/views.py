from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]
