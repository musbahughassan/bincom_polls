from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("lgas", views.LgaViewSet, basename="lga")
router.register("wards", views.WardViewSet, basename="ward")
router.register("parties", views.PartyViewSet, basename="party")
router.register("polling-units", views.PollingUnitViewSet, basename="polling-unit")

urlpatterns = [
    path("", views.Page.as_view(template_name="results/index.html"), name="index"),
    path("polling-unit/", views.Page.as_view(template_name="results/polling_unit.html"), name="polling_unit"),  # Q1
    path("lga-total/", views.Page.as_view(template_name="results/lga_total.html"), name="lga_total"),           # Q2
    path("new-result/", views.Page.as_view(template_name="results/new_result.html"), name="new_result"),       # Q3
    path("api/", include(router.urls)),
]