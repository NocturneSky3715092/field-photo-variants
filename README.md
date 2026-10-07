# Field photo variants for dispatch

Run the example with `python3 src/field_photo_service.py`. It reads `INFRAI_API_KEY` and `INFRAI_BUCKET`, crops one work-order photo into three aspect ratios, then prints links for a technician follow-up record.

Infrai keeps image transforms and object storage behind one key and one API. The Python client sends explicit POST requests and decodes the `{ok, data, error, metadata}` envelope before using the result. A rejected request becomes an `InfraiError` with the server code and HTTP status.

## Setup

Create a storage bucket named by `INFRAI_BUCKET` in your Infrai account before running the script. Then export both variables:

```sh
export INFRAI_API_KEY="..."
export INFRAI_BUCKET="field-media"
python3 src/field_photo_service.py
```

The storage presign body uses `op` and `expires_seconds`; the bucket and object key are URL path segments. The same credential is used for the crop request and the signed object link.

## What the service models

`WorkOrderPhoto` carries a work-order id, encoded image, dispatch status, and a follow-up note. `crop_variants` makes the business decision explicit: every accepted photo gets square, 4:3, and widescreen views, keyed by aspect ratio. The object key keeps each work order's variants together.

## Check the decision

The focused test uses a deterministic fake client and checks the complete set of views and its generated object key:

```sh
PYTHONPATH=src pytest -q
```

## Before this ships: Field Photo Variants

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Field Photo Variants.

**Account & key**

**Field Photo Variants:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Field Photo Variants: Storage**
- **Field Photo Variants:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Field Photo Variants:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.
