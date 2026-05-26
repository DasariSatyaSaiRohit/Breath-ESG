from django.urls import path
from .views import (
    RecordListView,
    RecordDetailView,
    RecordApproveView,
    RecordFlagView,
    RecordLockView,
    BulkApproveView,
)

urlpatterns = [
    path('', RecordListView.as_view(), name='record-list'),
    path('bulk-approve/', BulkApproveView.as_view(), name='record-bulk-approve'),
    path('lock/', RecordLockView.as_view(), name='record-lock'),
    path('<str:pk>/', RecordDetailView.as_view(), name='record-detail'),
    path('<str:pk>/approve/', RecordApproveView.as_view(), name='record-approve'),
    path('<str:pk>/flag/', RecordFlagView.as_view(), name='record-flag'),
]
