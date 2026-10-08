# Built by `sam build --use-container`, inside the Lambda build image.
# The python3.12 Lambda runtime lacks libexpat, which the rasterio wheel's GDAL needs; ship it in /opt/lib.
build-DepsLayer:
	pip install --no-cache-dir -r requirements.txt -t "$(ARTIFACTS_DIR)/python"
	mkdir -p "$(ARTIFACTS_DIR)/lib"
	cp -L /usr/lib64/libexpat.so.1 "$(ARTIFACTS_DIR)/lib/"
	find "$(ARTIFACTS_DIR)/python" -type d \( -name tests -o -name __pycache__ \) -prune -exec rm -rf {} +
