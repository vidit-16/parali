"""Where fields, claims, audit events and files live. LocalStore for the demo and tests, AwsStore on AWS."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Protocol


class Store(Protocol):
    def put(self, kind: str, id: str, item: dict) -> None: ...
    def get(self, kind: str, id: str) -> dict | None: ...
    def list(self, kind: str) -> list[dict]: ...
    def add_event(self, claim_id: str, event: dict) -> None: ...
    def events(self, claim_id: str) -> list[dict]: ...
    def put_blob(self, key: str, data: bytes, content_type: str) -> None: ...
    def get_blob(self, key: str) -> bytes | None: ...
    def blob_url(self, key: str) -> str: ...


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class LocalStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _path(self, kind: str, id: str) -> Path:
        return self.root / kind / f"{id}.json"

    def put(self, kind, id, item):
        p = self._path(kind, id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(item, indent=1, default=str), encoding="utf-8")

    def get(self, kind, id):
        p = self._path(kind, id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def list(self, kind):
        d = self.root / kind
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))] if d.exists() else []

    def add_event(self, claim_id, event):
        p = self.root / "events" / f"{claim_id}.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now_iso(), **event}, default=str) + "\n")

    def events(self, claim_id):
        p = self.root / "events" / f"{claim_id}.jsonl"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line]

    def put_blob(self, key, data, content_type):
        p = self.root / "blobs" / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get_blob(self, key):
        p = self.root / "blobs" / key
        return p.read_bytes() if p.exists() else None

    def blob_url(self, key):
        return f"/blobs/{key}"


class AwsStore:
    """One DynamoDB table (pk = KIND#id, sk = META or EVENT#time) and one S3 bucket."""

    def __init__(self, table_name: str, bucket: str, region: str | None = None, blob_prefix: str = "blobs/"):
        import boto3
        self.table = boto3.resource("dynamodb", region_name=region).Table(table_name)
        self.s3 = boto3.client("s3", region_name=region)
        self.bucket = bucket
        self.prefix = blob_prefix

    # Item bodies are stored as JSON text: DynamoDB rejects Python floats.
    def put(self, kind, id, item):
        self.table.put_item(Item={"pk": f"{kind}#{id}", "sk": "META", "kind": kind,
                                  "body": json.dumps(item, default=str)})

    def get(self, kind, id):
        r = self.table.get_item(Key={"pk": f"{kind}#{id}", "sk": "META"})
        return json.loads(r["Item"]["body"]) if "Item" in r else None

    def list(self, kind):
        from boto3.dynamodb.conditions import Key
        items, kw = [], {"IndexName": "kind-index", "KeyConditionExpression": Key("kind").eq(kind)}
        while True:
            r = self.table.query(**kw)
            items += [json.loads(i["body"]) for i in r["Items"]]
            if "LastEvaluatedKey" not in r:
                return items
            kw["ExclusiveStartKey"] = r["LastEvaluatedKey"]

    def add_event(self, claim_id, event):
        at = now_iso()
        self.table.put_item(Item={"pk": f"claims#{claim_id}", "sk": f"EVENT#{at}#{time.time_ns()}",
                                  "body": json.dumps({"at": at, **event}, default=str)})

    def events(self, claim_id):
        from boto3.dynamodb.conditions import Key
        r = self.table.query(KeyConditionExpression=Key("pk").eq(f"claims#{claim_id}") & Key("sk").begins_with("EVENT#"))
        return [json.loads(i["body"]) for i in r["Items"]]

    def put_blob(self, key, data, content_type):
        self.s3.put_object(Bucket=self.bucket, Key=self.prefix + key, Body=data, ContentType=content_type)

    def get_blob(self, key):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=self.prefix + key)["Body"].read()
        except self.s3.exceptions.NoSuchKey:
            return None

    def blob_url(self, key):
        return f"/blobs/{key}"
