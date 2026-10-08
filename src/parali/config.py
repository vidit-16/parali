STAC_URL = "https://earth-search.aws.element84.com/v1"
COLLECTION = "sentinel-2-c1-l2a"

# Read at 20 m. Visible bands are 10 m and get averaged down to the 20 m grid.
BANDS = ("red", "green", "blue", "nir08", "swir16", "swir22")

# SCL classes treated as unusable: no data, saturated, cloud medium/high, cirrus.
# Classes 2 (dark area) and 3 (shadow) are kept on purpose: Sen2Cor can put
# fresh burn scars there.
SCL_MASKED = (0, 1, 8, 9, 10)

PIXEL_SIZE_M = 20
FIELD_INNER_BUFFER_M = 20
MIN_FIELD_PIXELS = 8
