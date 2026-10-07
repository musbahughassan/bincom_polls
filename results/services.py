"""Small helpers shared by the serializers and viewsets."""
from .models import AnnouncedPuResult, Party

DELTA_STATE_ID = 25


def clean(text):
    """Collapse repeated whitespace (the dump has some double spaces)."""
    return " ".join((text or "").split())


def to_int(value):
    value = (value or "").strip()
    return int(value) if value.isdigit() and len(value) < 10 else None


def party_ids():
    """Party abbreviations in the order of the party table."""
    return [clean(p) for p in Party.objects.order_by("id").values_list("partyid", flat=True)]


def units_with_results():
    raw = AnnouncedPuResult.objects.values_list("polling_unit_uniqueid", flat=True).distinct()
    return {int(clean(r)) for r in raw if clean(r).isdigit()}


def unit_label(name, number, uniqueid, has_results=False):
    name, number = clean(name) or "Unnamed polling unit", clean(number)
    label = f"{name} - {number}" if number else name
    return f"{'✓ ' if has_results else ''}{label}  (ID {uniqueid})"


def ordered_scores(scores):
    """{stored abbreviation: score} -> [{"party", "score"}] in party-table order.

    announced_pu_results.party_abbreviation is CHAR(4), so the existing data stores
    LABOUR as 'LABO'. We match on the first 4 characters and show the full name.
    """
    rows, used = [], set()
    for party in party_ids():
        if party[:4] in scores:
            rows.append({"party": party, "score": scores[party[:4]]})
            used.add(party[:4])
    rows += [{"party": k, "score": v} for k, v in scores.items() if k not in used]
    return rows
