from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema_view, extend_schema

from customers.models import Customer
from customers.serializers import CustomerChangePasswordSerializer, CustomerSerializer


@extend_schema_view(
    list=extend_schema(
        summary="고객 목록 조회",
        description="페이지네이션 처리된 고객 목록을 조회합니다. </br> 어드민 권한이 필요합니다."),
    retrieve=extend_schema(
        summary="단일 고객 조회",
        description="고객 ID로 고객 정보를 조회합니다. </br> 어드민 권한이 필요합니다."),
    create=extend_schema(
        summary="고객 생성",
        description="새로운 고객을 생성합니다. </br> 어드민 권한이 필요합니다."),
    update=extend_schema(
        summary="고객 수정",
        description="고객 정보를 수정합니다. </br> 어드민 권한이 필요합니다."),
    partial_update=extend_schema(
        summary="고객 일부 수정",
        description="고객 정보를 일부 수정합니다. </br> 어드민 권한이 필요합니다."),
    destroy=extend_schema(
        summary="고객 삭제",
        description="고객 정보를 삭제합니다. </br> 어드민 권한이 필요합니다."),
)
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'change_password':
            return CustomerChangePasswordSerializer
        return CustomerSerializer

    def perform_create(self, serializer):
        customer = serializer.save()
        customer.set_password(customer.password)
        customer.save()

    @extend_schema(
        summary="고객 비밀번호 변경",
        description="고객의 비밀번호를 변경합니다. </br> 어드민 권한이 필요합니다.",
        responses={204: None},
    )
    @action(
        detail=True,
        methods=['post'],
        serializer_class=[CustomerChangePasswordSerializer],
        permission_classes=[IsAdminUser])
    def change_password(self, request, *args, **kwargs):
        customer = self.get_object()
        customer.set_password(request.data['password'])
        customer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
