package main

import (
	"context"
	"log"
	"net/http"
	"os"

	"github.com/datjax/vip-translate/word-inbox/backend/internal/api"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
)

func main() {
	addr := os.Getenv("PORT")
	if addr == "" {
		addr = "8088"
	}
	if os.Getenv("APP_PASSWORD") == "" {
		_ = os.Setenv("APP_PASSWORD", "dev-password")
	}
	if os.Getenv("APP_TOKEN") == "" {
		_ = os.Setenv("APP_TOKEN", "dev-token")
	}
	if os.Getenv("CORS_ORIGIN") == "" {
		_ = os.Setenv("CORS_ORIGIN", "*")
	}

	var st store.Store = store.NewMemoryStore()
	backend := "memory store"
	if bucket := os.Getenv("S3_BUCKET"); bucket != "" {
		s3Store, err := store.NewS3Store(context.Background())
		if err != nil {
			log.Fatalf("store: %v", err)
		}
		st = s3Store
		backend = "s3://" + bucket
		if endpoint := os.Getenv("S3_ENDPOINT"); endpoint != "" {
			backend += " via " + endpoint
		}
	}

	handler := &api.Handler{Store: st}
	log.Printf("word-inbox local API on http://localhost:%s (%s)", addr, backend)
	log.Printf("APP_PASSWORD=%s APP_TOKEN=%s", os.Getenv("APP_PASSWORD"), os.Getenv("APP_TOKEN"))
	if err := http.ListenAndServe(":"+addr, api.WithLogging(handler)); err != nil {
		log.Fatal(err)
	}
}
