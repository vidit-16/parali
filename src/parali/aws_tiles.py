"""Lambda entry point for one map block. The driver (scripts/build_tiles.py) sends the block and the region."""
import os

from shapely.geometry import shape

from parali import tiles

BUCKET = os.environ.get("BUCKET_NAME", "")
PREFIX = "tiles/"


def handler(event, context):
    region = shape(event["region"])
    bx, by = event["block"]
    return tiles.build_block(bx, by, region, tiles.S3Sink(BUCKET, PREFIX), workers=int(event.get("workers", 12)))
