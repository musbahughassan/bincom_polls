from datetime import datetime

from django.db import transaction
from django.db.models import Max
from rest_framework import serializers

from .models import AnnouncedPuResult, Lga, Party, PollingUnit, Ward
from .services import DELTA_STATE_ID, clean, ordered_scores, party_ids, unit_label


def latin1(value):
    """The dump's tables are latin1, so reject characters MySQL could not store."""
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        raise serializers.ValidationError("Please use standard Latin characters only.")


class LgaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lga
        fields = ("lga_id", "lga_name")


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ("uniqueid", "ward_name")


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ("partyid", "partyname")


class PollingUnitListSerializer(serializers.ModelSerializer):
    """Lightweight rows for the polling-unit combo box."""

    label = serializers.SerializerMethodField()
    has_results = serializers.SerializerMethodField()

    class Meta:
        model = PollingUnit
        fields = ("uniqueid", "label", "has_results")

    def get_has_results(self, obj):
        return obj.uniqueid in self.context["with_results"]

    def get_label(self, obj):
        return unit_label(obj.polling_unit_name, obj.polling_unit_number, obj.uniqueid, self.get_has_results(obj))


class PollingUnitDetailSerializer(serializers.ModelSerializer):
    """Question 1: one polling unit with each party's score."""

    class Meta:
        model = PollingUnit
        fields = ("uniqueid", "polling_unit_name", "polling_unit_number", "lga_id", "uniquewardid")

    def to_representation(self, obj):
        data = super().to_representation(obj)
        scores = {}
        for r in AnnouncedPuResult.objects.filter(polling_unit_uniqueid=str(obj.uniqueid)).values_list(
            "party_abbreviation", "party_score"
        ):
            scores[clean(r[0])] = scores.get(clean(r[0]), 0) + r[1]
        results = ordered_scores(scores)
        data.update(
            label=unit_label(obj.polling_unit_name, obj.polling_unit_number, obj.uniqueid),
            lga_name=Lga.objects.filter(lga_id=obj.lga_id).values_list("lga_name", flat=True).first(),
            ward_name=Ward.objects.filter(uniqueid=obj.uniquewardid).values_list("ward_name", flat=True).first(),
            results=results,
            total=sum(r["score"] for r in results),
        )
        return data


class PollingUnitCreateSerializer(serializers.ModelSerializer):
    """Question 3: create a new polling unit together with the scores of ALL parties."""

    polling_unit_name = serializers.CharField(max_length=50, validators=[latin1])
    polling_unit_number = serializers.CharField(max_length=50, required=False, allow_blank=True, validators=[latin1])
    polling_unit_description = serializers.CharField(required=False, allow_blank=True, validators=[latin1])
    entered_by_user = serializers.CharField(max_length=50, validators=[latin1])
    uniquewardid = serializers.IntegerField()
    scores = serializers.DictField(
        child=serializers.IntegerField(min_value=0, max_value=999_999_999), write_only=True
    )

    class Meta:
        model = PollingUnit
        fields = (
            "uniqueid", "lga_id", "uniquewardid", "polling_unit_name", "polling_unit_number",
            "polling_unit_description", "entered_by_user", "scores",
        )
        read_only_fields = ("uniqueid",)

    def validate_scores(self, value):
        expected = set(party_ids())
        errors = {p: "This score is required." for p in sorted(expected - set(value))}
        errors.update({p: "Unknown party." for p in sorted(set(value) - expected)})
        if errors:
            raise serializers.ValidationError(errors)
        return value

    def validate(self, data):
        if not Lga.objects.filter(lga_id=data["lga_id"], state_id=DELTA_STATE_ID).exists():
            raise serializers.ValidationError({"lga_id": "Select a Delta State local government."})
        if not Ward.objects.filter(uniqueid=data["uniquewardid"], lga_id=data["lga_id"]).exists():
            raise serializers.ValidationError({"uniquewardid": "That ward does not belong to the selected LGA."})
        return data

    @transaction.atomic
    def create(self, validated_data):
        scores = validated_data.pop("scores")
        ward = Ward.objects.get(uniqueid=validated_data["uniquewardid"])
        last = PollingUnit.objects.filter(uniquewardid=ward.uniqueid).aggregate(m=Max("polling_unit_id"))["m"] or 0
        now = datetime.now().replace(microsecond=0)
        pu = PollingUnit.objects.create(
            **validated_data, ward_id=ward.ward_id, polling_unit_id=last + 1, date_entered=now
        )
        AnnouncedPuResult.objects.bulk_create(
            AnnouncedPuResult(
                polling_unit_uniqueid=str(pu.uniqueid),
                party_abbreviation=party[:4],  # CHAR(4) column: LABOUR is stored as 'LABO', like the existing rows
                party_score=score,
                entered_by_user=pu.entered_by_user,
                date_entered=now,
                user_ip_address=pu.user_ip_address,
            )
            for party, score in scores.items()
        )
        return pu

    def to_representation(self, instance):
        return PollingUnitDetailSerializer(instance, context=self.context).data
