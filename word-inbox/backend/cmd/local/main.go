package main

import (
	"log"
	"net/http"
	"os"

	"github.com/datjax/vip-translate/word-inbox/backend/internal/api"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
)

func main() {
	addr := os.Getenv("PORT")
	if addr == "" {
		addr = "8080"
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

	handler := &api.Handler{Store: store.NewMemoryStore()}
	log.Printf("word-inbox local API on http://localhost:%s (memory store)", addr)
	log.Printf("APP_PASSWORD=%s APP_TOKEN=%s", os.Getenv("APP_PASSWORD"), os.Getenv("APP_TOKEN"))
	if err := http.ListenAndServe(":"+addr, handler); err != nil {
		log.Fatal(err)
	}
}
