"""Lambda entry points. Same api.handle and service functions as the local demo, with DynamoDB, S3, Polly and SNS."""
import base64
import json
import os
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key

from parali import firms, service
from parali.api import Deps, handle, officer_pin_from_env
from parali.area import AreaStack, fetch_area
from parali.payments import Razorpay, public_url
from parali.rules import Thresholds
from parali.store import AwsStore
from parali.tts import Voice

REGION = os.environ.get("AWS_REGION", "us-west-2")
TABLE = os.environ.get("TABLE_NAME", "")
BUCKET = os.environ.get("BUCKET_NAME", "")
PROCESS_FN = os.environ.get("PROCESS_FUNCTION", "")
TOPIC = os.environ.get("TOPIC_ARN", "")
PAD_DEG = 0.0018


@lru_cache(maxsize=1)
def store() -> AwsStore:
    return AwsStore(TABLE, BUCKET, REGION)


@lru_cache(maxsize=1)
def fires():
    p = Path("/tmp/firms.csv")
    if not p.exists():
        boto3.client("s3", region_name=REGION).download_file(BUCKET, "data/firms.csv", str(p))
    return firms.load(p)


def stacks(field, start, end) -> AreaStack:
    """Imagery for a field: S3 cache first, otherwise read Sentinel-2 COGs from the AWS Open Data bucket."""
    s3 = boto3.client("s3", region_name=REGION)
    key = f"stacks/{field.id}_{start}_{end}.npz"
    local = Path(f"/tmp/{field.id}_{start}_{end}.npz")
    try:
        s3.download_file(BUCKET, key, str(local))
        return AreaStack.load(local)
    except s3.exceptions.ClientError:
        pass
    x0, y0, x1, y1 = field.bbox
    bbox = (x0 - PAD_DEG, y0 - PAD_DEG, x1 + PAD_DEG, y1 + PAD_DEG)
    st = fetch_area(bbox, (start - timedelta(days=7)).isoformat(), end.isoformat(),
                    tile=field.props.get("tile"), log=print)
    st.save(local)
    s3.upload_file(str(local), BUCKET, key)
    return st


def _dispatch(claim_id: str) -> None:
    boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=PROCESS_FN, InvocationType="Event", Payload=json.dumps({"claim_id": claim_id}).encode())


def _dispatch_check(check_id: str) -> None:
    boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=PROCESS_FN, InvocationType="Event", Payload=json.dumps({"check_id": check_id}).encode())


def _reset() -> None:
    st = store()
    for c in st.list("claims"):
        for item in st.table.query(KeyConditionExpression=Key("pk").eq(f"claims#{c['id']}"))["Items"]:
            st.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
    s3 = boto3.resource("s3", region_name=REGION).Bucket(BUCKET)
    s3.objects.filter(Prefix="blobs/").delete()


def _speaker():
    return Voice(REGION)


def api_handler(event, context):
    http = event["requestContext"]["http"]
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif body:
        body = body.encode()
    deps = Deps(store=store(), dispatch=_dispatch, officer_pin=officer_pin_from_env(), speaker=_speaker(),
                reset=_reset, fires=fires, dispatch_check=_dispatch_check, notify=_notify_whatsapp, followup=_followup,
                payments=Razorpay.from_keys, base_url=public_url)
    status, headers, out = handle(http["method"], event["rawPath"], body, event.get("headers") or {}, deps,
                                  event.get("queryStringParameters") or {})
    return {"statusCode": status, "headers": headers, "body": out.decode()}


def _notify_whatsapp(claim: dict) -> int:
    """Farmers who chatted on WhatsApp hear the decision there too; a failure here never blocks the decision.
    Returns how many phones were told."""
    from parali import whatsapp
    try:
        cfg = whatsapp.config()
        if cfg.get("token"):
            return whatsapp.notify(store(), claim, whatsapp.Client(cfg))
    except Exception as e:
        print(f"whatsapp notify failed: {type(e).__name__}")
    return 0


def _followup(claim_id: str) -> None:
    boto3.client("lambda", region_name=REGION).invoke(
        FunctionName=PROCESS_FN, InvocationType="Event", Payload=json.dumps({"followup": claim_id}).encode())


def _notify(claim: dict) -> None:
    _notify_whatsapp(claim)
    if not TOPIC:
        return
    msg = claim.get("message", {})
    boto3.client("sns", region_name=REGION).publish(
        TopicArn=TOPIC, Subject=f"Claim {claim['id']}: {claim['status']}"[:100],
        Message=f"{claim['field_name']} ({claim['farmer_name']}): {claim['status']}\n\n{msg.get('en', '')}\n\n{msg.get('hi', '')}")


def process_handler(event, context):
    st = store()
    if event.get("followup"):
        c = service.after_decision(st, event["followup"], _speaker(), Razorpay.from_keys(), public_url(), _notify_whatsapp)
        return c["status"]
    if event.get("demo_reset"):  # daily: clear the demo and file one fresh claim per field, each in its own run
        from parali import season
        _reset()
        lam = boto3.client("lambda", region_name=REGION)
        for f in st.list("fields"):
            c = service.create_claim(st, f["id"], *season.SEASON)
            lam.invoke(FunctionName=context.invoked_function_arn, InvocationType="Event",
                       Payload=json.dumps({"claim_id": c["id"], "quiet": True}).encode())
        return "reset"
    th = Thresholds.load()
    if event.get("check_id"):
        from parali import check
        try:
            return check.run(st, event["check_id"], stacks, fires(), th)["status"]
        except Exception as e:
            item = st.get("checks", event["check_id"]) or {"id": event["check_id"]}
            item.update(status="error", error=str(e))
            st.put("checks", event["check_id"], item)
            raise
    if event.get("claim_id"):
        ids = [event["claim_id"]]
    else:  # scheduled sweep: anything still waiting for a decision
        ids = [c["id"] for c in st.list("claims") if c["status"] == "submitted"]
    done = []
    for cid in ids:
        try:
            c = service.run_season(st, cid, stacks, fires(), th, _speaker())
            if not event.get("quiet"):
                _notify(c)
            done.append({"id": cid, "status": c["status"]})
        except Exception as e:
            print(f"claim {cid} failed: {e!r}")
            c = st.get("claims", cid)
            if c:
                c["error"] = str(e)
                st.put("claims", cid, c)
            done.append({"id": cid, "error": str(e)})
    print(json.dumps(done))
    return done
