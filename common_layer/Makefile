build-CommonLayer:
	mkdir -p "$(ARTIFACTS_DIR)/python"
	cp -r python/* "$(ARTIFACTS_DIR)/python/"
	python -m pip install --no-cache-dir -r requirements.txt -t "$(ARTIFACTS_DIR)/python"
	cp .env "$(ARTIFACTS_DIR)/python/";

	@if [ "$(AWS_SAM_LOCAL)" = "true" ]; then \
		if [ -f .env ]; then \
			echo "Found .env, Copying to $(ARTIFACTS_DIR)/python/..."; \
			 \
			echo "Copied .env to layer for local development."; \
		else \
			echo "No .env file found at ../.env. Skipping copy."; \
		fi; \
	else \
		echo ".env not copied to layer for deployment."; \
	fi
