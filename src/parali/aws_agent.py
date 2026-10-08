"""Lambda for the farmer's voice assistant: /api/agent and /api/config.

Kept apart from parali.aws so it does not load the imagery stack (rasterio, numpy): this function ships
with the Strands Agents SDK and the Transcribe streaming SDK instead.
"""
import base64
import json
import os
from functools import lru_cache, partial

import boto3

from parali.agent import BedrockBackend
from parali.api import Deps, handle
from parali.speech import transcribe_pcm
from parali.store import AwsStore
from parali.tts import polly_mp3

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
        speaker=partial(polly_mp3, region=REGION),
        transcriber=partial(transcribe_pcm, region=REGION),
        agent_backend=BedrockBackend(region=REGION),
    )


def handler(event, context):
    http = event["requestContext"]["http"]
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    elif body:
        body = body.encode()
    status, headers, out = handle(http["method"], event["rawPath"], body, event.get("headers") or {}, _deps())
    return {"statusCode": status, "headers": headers, "body": out.decode()}
