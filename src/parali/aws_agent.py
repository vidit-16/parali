"""Lambda for the farmer's voice assistant: /api/agent, /api/config and the WhatsApp webhook.

Kept apart from parali.aws so it does not load the imagery stack (rasterio, numpy): this function ships
with the Strands Agents SDK and the Transcribe streaming SDK instead.
"""
import base64
import json
import os
from functools import lru_cache, partial

import boto3

from parali import sarvam, whatsapp
from parali.agent import BedrockBackend
from parali.api import Deps, handle
from parali.speech import transcribe_pcm
from parali.store import AwsStore
from parali.tts import Voice

REGION = os.environ.get("AWS_REGION", "us-west-2")


@lru_cache(maxsize=1)
def _deps() -> Deps:
    def dispatch(claim_id: str) -> None:
        boto3.client("lambda", region_name=REGION).invoke(
            FunctionName=os.environ["PROCESS_FUNCTION"], InvocationType="Event",
            Payload=json.dumps({"claim_id": claim_id}).encode())

    return Deps(
        store=AwsStore(os.environ["TABLE_NAME"], os.environ["BUCKET_NAME"], REGION),
        dispatch=dispatch,
        speaker=Voice(REGION),
        transcriber=partial(transcribe_pcm, region=REGION),
        agent_backend=BedrockBackend(region=REGION),
    )


def _whatsapp_webhook(event, context, body: bytes | None) -> dict:
    cfg = whatsapp.config()
    if event["requestContext"]["http"]["method"] == "GET":
        status, text = whatsapp.verify(event.get("queryStringParameters") or {}, cfg)
        return {"statusCode": status, "headers": {"Content-Type": "text/plain"}, "body": text}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    if not whatsapp.signature_ok(body or b"", headers.get("x-hub-signature-256", ""), cfg.get("app_secret", "")):
        return {"statusCode": 401, "body": ""}
    # answer Meta now; each message is handled in its own async run of this function
    for msg in whatsapp.messages(json.loads(body or b"{}")):
        boto3.client("lambda", region_name=REGION).invoke(
            FunctionName=context.invoked_function_arn, InvocationType="Event",
            Payload=json.dumps({"wa_message": msg}).encode())
    return {"statusCode": 200, "body": ""}


def _whatsapp_message(msg: dict) -> str:
    d = _deps()
    done = whatsapp.handle(d.store, msg, whatsapp.Client(whatsapp.config()), d.dispatch, backend=d.agent_backend,
                           voice=d.speaker, transcribe=sarvam.transcribe)
    print(json.dumps({"wa": msg["id"][-8:], "type": msg.get("type"), "done": done}))
    return done


def handler(event, context):
    if "wa_message" in event:
        return _whatsapp_message(event["wa_message"])
    if "wa_setup" in event:  # run once by hand: aws lambda invoke ... --payload '{"wa_setup": true}'
        return whatsapp.setup(whatsapp.config(), event.get("waba"))
    if "wa_profile" in event:  # run once by hand, with the picture as base64 (assets/whatsapp-profile.png)
        return whatsapp.set_profile(whatsapp.config(), base64.b64decode(event["wa_profile"]["png_b64"]),
                                    event["wa_profile"].get("about", ""), event["wa_profile"].get("description", ""))
    http = event["requestContext"]["http"]
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif body:
        body = body.encode()
    if event["rawPath"] == "/api/whatsapp":
        return _whatsapp_webhook(event, context, body)
    status, headers, out = handle(http["method"], event["rawPath"], body, event.get("headers") or {}, _deps())
    return {"statusCode": status, "headers": headers, "body": out.decode()}
