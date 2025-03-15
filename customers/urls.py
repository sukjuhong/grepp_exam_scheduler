from django.urls import path

from customers.views import CustomerViewSet


urlpatterns = [
    path('', CustomerViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='customers'),
    path('<int:pk>/', CustomerViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='customer-detail'),
    path('<int:pk>/change-password/', CustomerViewSet.as_view({
        'post': 'change_password'
    }), name='customer-change-password'),
]
