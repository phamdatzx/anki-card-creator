.PHONY: tidy build-lambda zip-lambda run-local test

tidy:
	go mod tidy

run-local:
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
