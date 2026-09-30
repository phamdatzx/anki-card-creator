package main

import (
	"context"
	"log"

	"github.com/aws/aws-lambda-go/lambda"
	"github.com/awslabs/aws-lambda-go-api-proxy/httpadapter"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/api"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
)

func main() {
	ctx := context.Background()
	s3Store, err := store.NewS3Store(ctx)
	if err != nil {
		log.Fatalf("store: %v", err)
	}
	handler := &api.Handler{Store: s3Store}
	lambda.Start(httpadapter.NewV2(api.WithLogging(handler)).ProxyWithContext)
}
