.PHONY: tidy build-lambda zip-lambda run-local run-memory test

tidy:
	go mod tidy

# Local API backed by the docker compose S3 (LocalStack): `docker compose up -d` in ../
run-local:
	APP_PASSWORD=$${APP_PASSWORD:-dev-password} \
	APP_TOKEN=$${APP_TOKEN:-dev-token} \
	CORS_ORIGIN=$${CORS_ORIGIN:-*} \
	S3_BUCKET=$${S3_BUCKET:-word-inbox-local} \
	S3_ENDPOINT=$${S3_ENDPOINT:-http://localhost:$${S3_PORT:-4567}} \
	AWS_REGION=$${AWS_REGION:-us-east-1} \
	AWS_ACCESS_KEY_ID=test \
	AWS_SECRET_ACCESS_KEY=test \
	go run ./cmd/local

# Local API with an in-memory store (no Docker; batches are lost on exit).
run-memory:
	APP_PASSWORD=$${APP_PASSWORD:-dev-password} \
	APP_TOKEN=$${APP_TOKEN:-dev-token} \
	CORS_ORIGIN=$${CORS_ORIGIN:-*} \
	go run ./cmd/local

build-lambda:
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -tags lambda.norpc -o bootstrap ./cmd/lambda

zip-lambda: build-lambda
	python3 -c "import zipfile; z=zipfile.ZipFile('function.zip','w',zipfile.ZIP_DEFLATED); z.write('bootstrap'); z.close()"
	@echo "Created function.zip — upload as Lambda handler 'bootstrap'"

test:
	go test ./...
