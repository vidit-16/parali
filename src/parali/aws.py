"""Lambda entry points. Same api.handle and service functions as the local demo, with DynamoDB, S3, Polly and SNS."""
import base64
import json
import os
from datetime import timedelta
from functools import lru_cache, partial
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key

from parali import firms, service
from parali.api import Deps, handle, officer_pin_from_env
from parali.area import AreaStack, fetch_area
from parali.rules import Thresholds
from parali.store import AwsStore
from parali.tts import polly_mp3

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


def _reset() -> None:
    st = store()
    for c in st.list("claims"):
        for item in st.table.query(KeyConditionExpression=Key("pk").eq(f"claims#{c['id']}"))["Items"]:
            st.table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
    s3 = boto3.resource("s3", region_name=REGION).Bucket(BUCKET)
    s3.objects.filter(Prefix="blobs/").delete()


def _speaker():
    return partial(polly_mp3, region=REGION)


def api_handler(event, context):
    http = event["requestContext"]["http"]
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif body:
        body = body.encode()
    deps = Deps(store=store(), dispatch=_dispatch, officer_pin=officer_pin_from_env(), speaker=_speaker(),
                reset=_reset)
    status, headers, out = handle(http["method"], event["rawPath"], body, event.get("headers") or {}, deps)
    return {"statusCode": status, "headers": headers, "body": out.decode()}


def _notify(claim: dict) -> None:
    if not TOPIC:
        return
    msg = claim.get("message", {})
    boto3.client("sns", region_name=REGION).publish(
        TopicArn=TOPIC, Subject=f"Claim {claim['id']}: {claim['status']}"[:100],
        Message=f"{claim['field_name']} ({claim['farmer_name']}): {claim['status']}\n\n{msg.get('en', '')}\n\n{msg.get('hi', '')}")


def process_handler(event, context):
    st = store()
    th = Thresholds.load()
    if event.get("claim_id"):
        ids = [event["claim_id"]]
    else:  # scheduled sweep: anything still waiting for a decision
        ids = [c["id"] for c in st.list("claims") if c["status"] == "submitted"]
    done = []
    for cid in ids:
        try:
            c = service.run_season(st, cid, stacks, fires(), th, _speaker())
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
