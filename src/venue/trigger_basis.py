"""Does Bitget trigger conditional orders on LAST price or MARK price?

WHY IT MATTERS AND WHY IT IS RETRIEVED BEFORE THE RULE IS WRITTEN. This
project's OHLCV is LAST price. If the venue triggers stops on MARK price, every
stop in the backtest fires at a different instant than it would live, and mark
price is smoother than last, so the backtest would systematically misstate
stop-outs in a direction that cannot be signed without knowing the answer. The
exit specification depends on this, so it is retrieved first.

THE METHOD IS REPORT 25's, FOLLOWED EXACTLY. Documentation pages are discovered
rather than hardcoded; every response body is written to disk VERBATIM before
any parsing happens; the SHA-256 of each file is recorded in a manifest with the
request URL, the parameters and the UTC retrieval time; and anything requiring
authentication is recorded as UNAVAILABLE rather than approximated.

WHAT WAS ESTABLISHED. The trigger basis is a PER-ORDER PARAMETER, `triggerType`,
taking `fill_price` (the fill or last price) or `market_price` / `mark_price`
(the mark price). On the stop-profit / stop-loss endpoint -- the one that places
the orders this project needs -- it is OPTIONAL and the documentation declares
its default as `fill_price`. On the plain trigger-order endpoints it is
REQUIRED, so no default applies there.

WHAT REMAINS OUTSIDE THIS RETRIEVAL. Placing an order requires a signed request,
so the default's BEHAVIOUR is read from documentation and not confirmed against
a live order. The default is parsed from Bitget's own STATIC v1 documentation
mirror; the v2 pages could not be parsed (below), so the v2 default is not
independently corroborated. Both boundaries are stated in the design document
rather than smoothed over.

THE v2 DOCUMENTATION PAGES ARE JS-RENDERED. `www.bitget.com/api-doc/...` returns
an application shell to an automated fetch and no endpoint content -- the same
finding report 25 recorded, and `src/costs/build_fee_artifact.py` before it for
`www.bitget.com/fee`. Their responses are snapshotted anyway, because "the page
carried no content" is itself a fact worth being able to re-check. The parameter
is read from Bitget's own STATIC v1 documentation mirror, which is served as
plain HTML and does carry it.

NO MARKET DATA IS READ. This module touches no bar at any resolution, and a test
asserts it cannot reach the data layer.
"""

import hashlib
import html
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from config import settings  # noqa: E402

SNAPSHOT_DIR = os.path.join(ROOT, "data", "reference", "bitget_venue")
MANIFEST_PATH = os.path.join(SNAPSHOT_DIR, "trigger_basis_manifest.json")

USER_AGENT = "crypto-bot/trigger-basis"
TIMEOUT_S = 30
MIN_INTERVAL = 1.0 / settings.MAX_REQUESTS_PER_SECOND
MAX_ATTEMPTS = 4
BASE_BACKOFF = 0.5
RETRY_HTTP = {429}

_last_request_ts = 0.0

#: The pages consulted, each with what it was expected to carry. Discovered by
#: searching Bitget's own documentation index, not hardcoded from memory.
SOURCES = {
    "v1_mix_doc": {
        "url": "https://bitgetlimited.github.io/apidoc/en/mix/",
        "kind": "documentation",
        "note": "Bitget's own STATIC v1 mix documentation mirror, served as "
                "plain HTML. Carries the triggerType parameter and its "
                "allowed values.",
    },
    "v2_place_tpsl": {
        "url": "https://www.bitget.com/api-doc/contract/plan/Place-Tpsl-Order",
        "kind": "documentation",
        "note": "The v2 stop-profit / stop-loss endpoint page. JS-rendered; "
                "snapshotted to record that it carries no endpoint content to "
                "an automated fetch.",
    },
    "v2_place_plan": {
        "url": "https://www.bitget.com/api-doc/contract/plan/Place-Plan-Order",
        "kind": "documentation",
        "note": "The v2 trigger-order endpoint page. Same JS-rendering caveat.",
    },
}

#: The parameter this retrieval exists to establish, and the two values the
#: documentation defines for it. TRANSCRIBED FROM THE RETRIEVED PAGE by
#: `parse_trigger_basis`, never asserted here.
PARAMETER_NAME = "triggerType"
LAST_PRICE_TOKEN = "fill_price"
MARK_PRICE_TOKEN_V1 = "market_price"
MARK_PRICE_TOKEN_V2 = "mark_price"

UNRETRIEVED = "UNRETRIEVED"


class RetrievalFailed(Exception):
    """The page could not be reached, or answered with something unusable."""


class SchemaError(Exception):
    """A snapshot is missing content the report depends on.

    Separate from RetrievalFailed because they mean different things: one says
    the network is wrong, the other says our reading of the page is wrong. A
    parser that defaulted a missing value would report a trigger basis the
    venue never documented.
    """


def stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _throttle():
    global _last_request_ts
    wait = MIN_INTERVAL - (time.monotonic() - _last_request_ts)
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.monotonic()


def fetch_raw(url):
    """One throttled, retrying GET. Returns (final_url, status, body_text)."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        _throttle()
        try:
            resp = requests.get(url, timeout=TIMEOUT_S,
                                headers={"User-Agent": USER_AGENT})
        except requests.RequestException as exc:
            if attempt < MAX_ATTEMPTS:
                time.sleep(BASE_BACKOFF * (2 ** (attempt - 1))
                           + random.uniform(0, 0.25))
                continue
            raise RetrievalFailed("network failure contacting %s after %d "
                                  "attempts: %r" % (url, MAX_ATTEMPTS, exc))
        if resp.status_code == 200:
            return resp.url, resp.status_code, resp.text
        retryable = resp.status_code in RETRY_HTTP or 500 <= resp.status_code < 600
        if not retryable:
            raise RetrievalFailed("non-retryable HTTP %s from %s"
                                  % (resp.status_code, url))
        if attempt < MAX_ATTEMPTS:
            time.sleep(BASE_BACKOFF * (2 ** (attempt - 1))
                       + random.uniform(0, 0.25))
    raise RetrievalFailed("HTTP error persisted at %s after %d attempts"
                          % (url, MAX_ATTEMPTS))


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_name(key):
    return "trigger_basis__%s.html" % key


def write_raw(key, text, snapshot_dir=SNAPSHOT_DIR):
    """Write the body verbatim and return (path, sha256)."""
    os.makedirs(snapshot_dir, exist_ok=True)
    path = os.path.join(snapshot_dir, snapshot_name(key))
    with open(path, "wb") as fh:
        fh.write(text.encode("utf-8"))
    return path, sha256_of(path)


def retrieve(sources=None, snapshot_dir=SNAPSHOT_DIR,
             manifest_path=MANIFEST_PATH):
    """Fetch every page, snapshot raw, write the manifest. RAW BEFORE PARSED."""
    sources = SOURCES if sources is None else sources
    retrieved_at = stamp()
    calls = []
    for key, meta in sources.items():
        final_url, status, text = fetch_raw(meta["url"])
        path, digest = write_raw(key, text, snapshot_dir)
        calls.append({
            "key": key,
            "requested_url": meta["url"],
            "final_url": final_url,
            "params": {},
            "kind": meta["kind"],
            "note": meta["note"],
            "http_status": status,
            "retrieved_at_utc": stamp(),
            "snapshot_file": os.path.basename(path),
            "sha256": digest,
            "bytes": os.path.getsize(path),
        })
    manifest = {
        "retrieved_at_utc": retrieved_at,
        "question": "Does Bitget trigger conditional stop and take-profit "
                    "orders on LAST price or MARK price, and is that a default "
                    "or a per-order parameter?",
        "retrieval_method": "automated, public pages, no credentials",
        "authentication_note": (
            "The trigger basis is a PER-ORDER parameter on the order-placement "
            "endpoints, and placing an order requires a SIGNED request. The "
            "parameter's name and allowed values are publicly documented and "
            "are retrieved here; its behaviour when OMITTED cannot be "
            "established without credentials and is recorded as unretrieved."),
        "calls": calls,
    }
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return manifest


def load_manifest(manifest_path=MANIFEST_PATH):
    if not os.path.exists(manifest_path):
        raise RetrievalFailed(
            "no trigger-basis snapshot at %s; run "
            "`python -m src.venue.trigger_basis`" % manifest_path)
    with open(manifest_path) as fh:
        return json.load(fh)


def load_raw(key, snapshot_dir=SNAPSHOT_DIR):
    """Read one snapshot back. THE PARSING PATH STARTS ON DISK."""
    path = os.path.join(snapshot_dir, snapshot_name(key))
    if not os.path.exists(path):
        raise SchemaError("snapshot file missing: %s" % path)
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Parsing. Every field the document depends on is required.
# ---------------------------------------------------------------------------

def plain_text(html_text):
    """Tags stripped, ENTITIES UNESCAPED, whitespace collapsed.

    The unescaping is load-bearing: the documentation renders the default value
    as `&#39;fill_price&#39;`, so a parser that left entities encoded would find
    the parameter, find its values, and silently miss the one row that declares
    a default.
    """
    return re.sub(r"\s+", " ",
                  html.unescape(re.sub(r"<[^>]+>", " ", html_text)))


#: The parameter row as the v1 documentation renders it, after tag stripping:
#:     triggerType String No Trigger Type default 'fill_price'
#:     triggerType String Yes Trigger type
#: The optional trailing group is the DOCUMENTED DEFAULT, and its presence is
#: what distinguishes an endpoint that has one from an endpoint that requires
#: the parameter outright.
_ROW = re.compile(
    r"triggerType\s+String\s+(?P<required>Yes|No)\s+Trigger\s*[Tt]ype"
    r"(?:\s+default\s+['\"](?P<default>[a-z_]+)['\"])?")


def parse_trigger_basis(text, source_key="v1_mix_doc"):
    """What the retrieved page says about the trigger basis.

    REQUIRES the parameter name and both value tokens to be PRESENT. A page
    that does not carry them raises rather than returning an empty finding: an
    empty finding would be reported as "the venue documents no trigger basis",
    which is the most dangerous sentence this retrieval could produce.

    THE DEFAULT IS PARSED WHERE THE PAGE STATES ONE and reported as
    UNRETRIEVED where it does not. The parameter appears on several endpoints
    and they do not agree: some require it, one declares a default. Both facts
    are returned rather than collapsed into a single answer.
    """
    if not isinstance(text, str) or len(text) < 1_000:
        raise SchemaError("%s: snapshot is empty or truncated (%d bytes)"
                          % (source_key, len(text or "")))
    if PARAMETER_NAME not in text:
        raise SchemaError(
            "%s: the parameter %r is absent from the snapshot; the page's "
            "schema may have changed or the wrong page was retrieved"
            % (source_key, PARAMETER_NAME))

    flat = plain_text(text)
    values = []
    for token in (LAST_PRICE_TOKEN, MARK_PRICE_TOKEN_V1, MARK_PRICE_TOKEN_V2):
        if re.search(re.escape(token), flat):
            values.append(token)
    if LAST_PRICE_TOKEN not in values:
        raise SchemaError("%s: the last-price token %r is absent"
                          % (source_key, LAST_PRICE_TOKEN))
    if not ({MARK_PRICE_TOKEN_V1, MARK_PRICE_TOKEN_V2} & set(values)):
        raise SchemaError("%s: no mark-price token is present" % source_key)

    rows = [{"required": m.group("required") == "Yes",
             "default": m.group("default")} for m in _ROW.finditer(flat)]
    if not rows:
        raise SchemaError("%s: the parameter is named but no parameter ROW "
                          "was found; the page's table layout may have changed"
                          % source_key)
    defaults = sorted({r["default"] for r in rows if r["default"]})
    if len(defaults) > 1:
        raise SchemaError("%s: the page declares more than one default for "
                          "%r: %s" % (source_key, PARAMETER_NAME, defaults))

    return {
        "source": source_key,
        "parameter_name": PARAMETER_NAME,
        "values_found": values,
        "last_price_token": LAST_PRICE_TOKEN,
        "mark_price_tokens": [v for v in values if v != LAST_PRICE_TOKEN],
        "selectable_per_order": True,
        "parameter_rows": len(rows),
        "rows_requiring_it": sum(1 for r in rows if r["required"]),
        "rows_with_a_default": sum(1 for r in rows if r["default"]),
        "documented_default": defaults[0] if defaults else UNRETRIEVED,
        "default_is_last_price": bool(defaults) and defaults[0] == LAST_PRICE_TOKEN,
    }


def carries_endpoint_content(text):
    """Did a v2 documentation page return endpoint content, or a shell?

    Report 25 recorded that these pages are JS-rendered and answer an automated
    fetch with an application shell. The snapshot is kept so that claim can be
    re-checked rather than taken on trust.
    """
    return PARAMETER_NAME in text


def summarise(snapshot_dir=SNAPSHOT_DIR):
    """The finding, read back from disk."""
    finding = parse_trigger_basis(load_raw("v1_mix_doc", snapshot_dir))
    shells = {key: not carries_endpoint_content(load_raw(key, snapshot_dir))
              for key in ("v2_place_tpsl", "v2_place_plan")}
    finding["v2_pages_returned_a_shell"] = shells
    return finding


def main(argv=None):
    print("retrieving the conditional-order trigger basis")
    for key, meta in SOURCES.items():
        print("  %s  %s" % (key, meta["url"]))
    manifest = retrieve()
    print("snapshot: %d files under %s" % (len(manifest["calls"]),
                                           SNAPSHOT_DIR))
    finding = summarise()
    print("parameter          : %s" % finding["parameter_name"])
    print("values documented  : %s" % ", ".join(finding["values_found"]))
    print("selectable per order: %s" % finding["selectable_per_order"])
    print("default when omitted: %s" % finding["default_when_omitted"])
    print("v2 pages a shell   : %s" % finding["v2_pages_returned_a_shell"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
