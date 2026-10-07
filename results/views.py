from django.db.models import Sum
from django.views.generic import TemplateView
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AnnouncedPuResult, Lga, Party, PollingUnit, Ward
from .serializers import (
    LgaSerializer, PartySerializer, PollingUnitCreateSerializer,
    PollingUnitDetailSerializer, PollingUnitListSerializer, WardSerializer,
)
from .services import DELTA_STATE_ID, clean, ordered_scores, to_int, units_with_results


class LgaViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/lgas/  and  /api/lgas/<lga_id>/  (Delta State only)."""

    queryset = Lga.objects.filter(state_id=DELTA_STATE_ID).order_by("lga_name")
    serializer_class = LgaSerializer
    lookup_field = "lga_id"

    @action(detail=True)
    def total(self, request, lga_id=None):
        """Question 2: summed result of all polling units in the LGA.

        Computed from announced_pu_results, NOT from announced_lga_results.
        """
        lga = self.get_object()
        unit_ids = [str(i) for i in PollingUnit.objects.filter(lga_id=lga.lga_id).values_list("uniqueid", flat=True)]
        rows = AnnouncedPuResult.objects.filter(polling_unit_uniqueid__in=unit_ids)
        totals = {
            clean(r["party_abbreviation"]): r["total"]
            for r in rows.values("party_abbreviation").annotate(total=Sum("party_score")).order_by()
        }
        scores = ordered_scores(totals)
        return Response(
            {
                "lga_id": lga.lga_id,
                "lga_name": lga.lga_name,
                "units_counted": rows.values("polling_unit_uniqueid").distinct().count(),
                "units_in_lga": len(unit_ids),
                "scores": scores,
                "total": sum(s["score"] for s in scores),
            }
        )


class WardViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/wards/?lga=<lga_id>[&with_units=1]"""

    serializer_class = WardSerializer

    def get_queryset(self):
        qs = Ward.objects.order_by("ward_name")
        raw = self.request.query_params.get("lga")
        if raw is None:
            return qs
        lga_id = to_int(raw)
        if lga_id is None:
            return qs.none()
        if self.request.query_params.get("with_units") == "1":  # only wards that contain polling units
            return qs.filter(uniqueid__in=PollingUnit.objects.filter(lga_id=lga_id).values("uniquewardid"))
        return qs.filter(lga_id=lga_id)


class PartyViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """GET /api/parties/"""

    queryset = Party.objects.order_by("id")
    serializer_class = PartySerializer


class PollingUnitViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    GET  /api/polling-units/?lga=<lga_id>&ward=<ward uniqueid>   list (combo box)
    GET  /api/polling-units/<uniqueid>/                          Question 1
    POST /api/polling-units/                                     Question 3
    (no update/delete: the mixins we left out are the endpoints we do not offer)
    """

    def get_queryset(self):
        qs = PollingUnit.objects.filter(uniquewardid__gt=0).order_by("polling_unit_name", "uniqueid")
        for param, field in (("lga", "lga_id"), ("ward", "uniquewardid")):
            raw = self.request.query_params.get(param)
            if raw is not None:
                value = to_int(raw)
                qs = qs.filter(**{field: value}) if value is not None else qs.none()
        return qs

    def get_serializer_class(self):
        return {"list": PollingUnitListSerializer, "create": PollingUnitCreateSerializer}.get(
            self.action, PollingUnitDetailSerializer
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "list":
            context["with_results"] = units_with_results()
        return context

    def perform_create(self, serializer):
        serializer.save(user_ip_address=self.request.META.get("REMOTE_ADDR", "")[:50])


class Page(TemplateView):
    """The three HTML pages; all data comes from the API above."""