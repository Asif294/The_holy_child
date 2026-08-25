from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.fees.views import FeeCategoryViewSet, FeeStructureViewSet, InvoiceViewSet, PaymentViewSet

router = DefaultRouter()
router.register("fee-categories", FeeCategoryViewSet, basename="fee-category")
router.register("fee-structures", FeeStructureViewSet, basename="fee-structure")
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [path("", include(router.urls))]
