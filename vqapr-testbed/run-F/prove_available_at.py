"""Prove the documented KRX close localization before slice conversion."""

from datetime import datetime, timedelta, timezone

import pyarrow as pa
import pyarrow.compute as pc

KNOWN_WALL_TIME = datetime(2015, 1, 2, 15, 0)
localized = pc.assume_timezone(
    pa.array([KNOWN_WALL_TIME], type=pa.timestamp("us")),
    "Asia/Seoul",
)[0].as_py()
round_trip = localized.astimezone(timezone.utc).astimezone(localized.tzinfo)

assert localized.date().isoformat() == "2015-01-02"
assert localized.time().isoformat() == "15:00:00"
assert localized.utcoffset() == timedelta(hours=9)
assert localized.astimezone(timezone.utc).isoformat() == "2015-01-02T06:00:00+00:00"
assert round_trip == localized

print(
    {
        "source_row": "A000020 @ 2015-01-02",
        "local": localized.isoformat(),
        "utc": localized.astimezone(timezone.utc).isoformat(),
        "round_trip": round_trip.isoformat(),
        "proved": True,
    }
)
