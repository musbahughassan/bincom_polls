"""Unmanaged models mapped onto the tables that already exist in bincom_test.sql.

managed = False  ->  Django never creates/alters these tables.
Only the columns this project needs are mapped.
"""
from django.db import models


class Lga(models.Model):
    uniqueid = models.AutoField(primary_key=True)
    lga_id = models.IntegerField()          # <- polling_unit.lga_id points HERE (not to uniqueid)
    lga_name = models.CharField(max_length=50)
    state_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "lga"


class Ward(models.Model):
    uniqueid = models.AutoField(primary_key=True)  # <- polling_unit.uniquewardid points here
    ward_id = models.IntegerField()                # NOT unique on its own
    ward_name = models.CharField(max_length=50)
    lga_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = "ward"


class PollingUnit(models.Model):
    uniqueid = models.AutoField(primary_key=True)
    polling_unit_id = models.IntegerField()
    ward_id = models.IntegerField()
    lga_id = models.IntegerField()
    uniquewardid = models.IntegerField(null=True)
    polling_unit_number = models.CharField(max_length=50, null=True, blank=True)
    polling_unit_name = models.CharField(max_length=50, null=True, blank=True)
    polling_unit_description = models.TextField(null=True, blank=True)
    entered_by_user = models.CharField(max_length=50, null=True, blank=True)
    date_entered = models.DateTimeField(null=True, blank=True)
    user_ip_address = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "polling_unit"


class Party(models.Model):
    id = models.AutoField(primary_key=True)
    partyid = models.CharField(max_length=11)
    partyname = models.CharField(max_length=11)

    class Meta:
        managed = False
        db_table = "party"


class AnnouncedPuResult(models.Model):
    result_id = models.AutoField(primary_key=True)
    # varchar in the database; holds polling_unit.uniqueid (NOT polling_unit_id)
    polling_unit_uniqueid = models.CharField(max_length=50)
    party_abbreviation = models.CharField(max_length=4)
    party_score = models.IntegerField()
    entered_by_user = models.CharField(max_length=50)
    date_entered = models.DateTimeField()
    user_ip_address = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "announced_pu_results"