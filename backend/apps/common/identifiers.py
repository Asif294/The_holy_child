"""
Sequential, human-readable identifiers — student IDs, admission numbers and
employee IDs.

These codes go on paperwork the office hands out, so they are a readable
running number (``THC-T-0007``) rather than a UUID, and the next one is offered
to the form up front: the clerk sees what will be issued, and can still type
something else over it.

The next number is derived from the rows already stored rather than from a
separate counter table — there is no second source of truth to drift out of
step, and a code is never handed out twice, because a soft-deleted row keeps
the code it was issued.
"""
import re
from datetime import date

from django.db import IntegrityError, transaction

#: How many times a generated code is recomputed after losing a race.
MAX_ATTEMPTS = 5


def next_code(model, field: str, prefix: str, width: int = 4) -> str:
    """
    The next free ``<prefix><number>`` code for ``model.field``.

    Only codes that match the prefix *and* end in digits count towards the
    running number, so a hand-typed ``THC-T-TEMP`` sitting in the table cannot
    poison the sequence.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$", re.IGNORECASE)
    stored = model.objects.filter(**{f"{field}__istartswith": prefix}).values_list(field, flat=True)

    highest = 0
    for code in stored:
        match = pattern.match((code or "").strip())
        if match:
            highest = max(highest, int(match.group(1)))

    return f"{prefix}{highest + 1:0{width}d}"


def create_with_generated_codes(create, validated_data, generators, attempts: int = MAX_ATTEMPTS):
    """
    Calls ``create(data)`` with any blank code field filled in from ``generators``.

    Two clerks admitting a student at the same moment are shown the same next
    number, and the database — not this function — decides which of them got
    it. The one who lost is retried with a freshly computed number rather than
    being shown a clash for a code they never typed.

    A code the caller *did* type is left exactly as given: if that one clashes,
    the error is theirs to see and fix.
    """
    blank = [name for name in generators if not validated_data.get(name)]
    if not blank:
        return create(validated_data)

    last_attempt = attempts - 1
    for attempt in range(attempts):
        data = dict(validated_data)
        for name in blank:
            data[name] = generators[name]()
        try:
            # Savepointed so a failed insert leaves the transaction usable and
            # the next attempt can run its own queries.
            with transaction.atomic():
                return create(data)
        except IntegrityError:
            if attempt == last_attempt:
                raise


def academic_year() -> str:
    """
    The year that dates this year's codes.

    The current academic session wins — a school still admitting into the 2026
    session in January 2027 should keep issuing ``THC-2026-…`` — and the
    calendar year is the fallback when no session is marked current.
    """
    from apps.classes.models import AcademicSession

    session = AcademicSession.current()
    if session:
        match = re.search(r"(\d{4})", session.name or "")
        if match:
            return match.group(1)
    return str(date.today().year)
