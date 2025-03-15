from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action

from customers.models import Customer
from customers.serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        user = serializer.save()
        user.set_password(user.password)
        user.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def change_password(self, request, *args, **kwargs):
        user = self.get_object()
        user.set_password(request.data['password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
