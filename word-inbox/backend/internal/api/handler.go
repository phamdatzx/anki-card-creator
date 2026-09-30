package api

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/datjax/vip-translate/word-inbox/backend/internal/auth"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/model"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
	"github.com/google/uuid"
)

type Handler struct {
	Store store.Store
}

type loginRequest struct {
	Password string `json:"password"`
}

type loginResponse struct {
	Token string `json:"token"`
}

// MaxBatchSize caps how many words one send may contain.
const MaxBatchSize = 200

type createBatchRequest struct {
	Words []model.Word `json:"words"`
}

type createBatchResponse struct {
	ID        string    `json:"id"`
	CreatedAt time.Time `json:"createdAt"`
	Count     int       `json:"count"`
}

type errorResponse struct {
	Error string `json:"error"`
}

func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	h.applyCORS(w, r)
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	path := strings.TrimSuffix(r.URL.Path, "/")
	if path == "" {
		path = "/"
	}

	switch {
	case r.Method == http.MethodPost && path == "/login":
		h.login(w, r)
	case r.Method == http.MethodPost && path == "/words":
		h.createBatch(w, r)
	default:
		writeJSON(w, http.StatusNotFound, errorResponse{Error: "not found"})
	}
}

func (h *Handler) applyCORS(w http.ResponseWriter, r *http.Request) {
	origin := os.Getenv("CORS_ORIGIN")
	if origin == "" {
		origin = "*"
	}
	reqOrigin := r.Header.Get("Origin")
	if origin == "*" {
		w.Header().Set("Access-Control-Allow-Origin", "*")
	} else if reqOrigin == origin {
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Vary", "Origin")
	} else if reqOrigin != "" && origin != "*" {
		// Still echo configured origin when present so browsers can reject.
		w.Header().Set("Access-Control-Allow-Origin", origin)
		w.Header().Set("Vary", "Origin")
	}
	w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
}

func (h *Handler) login(w http.ResponseWriter, r *http.Request) {
	var req loginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid JSON body"})
		return
	}
	if !auth.CheckPassword(req.Password) {
		writeJSON(w, http.StatusUnauthorized, errorResponse{Error: "invalid password"})
		return
	}
	token := auth.Token()
	if token == "" {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: "APP_TOKEN is not configured"})
		return
	}
	writeJSON(w, http.StatusOK, loginResponse{Token: token})
}

func (h *Handler) createBatch(w http.ResponseWriter, r *http.Request) {
	if !auth.RequireBearer(r) {
		writeJSON(w, http.StatusUnauthorized, errorResponse{Error: "unauthorized"})
		return
	}
	var req createBatchRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid JSON body"})
		return
	}
	if len(req.Words) == 0 {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "words is required"})
		return
	}
	if len(req.Words) > MaxBatchSize {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: fmt.Sprintf("at most %d words per batch", MaxBatchSize)})
		return
	}
	words := make([]model.Word, 0, len(req.Words))
	for i, item := range req.Words {
		input := strings.TrimSpace(item.Input)
		wordType := strings.TrimSpace(item.Type)
		if wordType == "" {
			wordType = model.TypeNormal
		}
		if input == "" {
			writeJSON(w, http.StatusBadRequest, errorResponse{Error: fmt.Sprintf("words[%d]: input is required", i)})
			return
		}
		if !model.ValidType(wordType) {
			writeJSON(w, http.StatusBadRequest, errorResponse{Error: fmt.Sprintf("words[%d]: invalid type", i)})
			return
		}
		words = append(words, model.Word{Input: input, Type: wordType})
	}
	batch := model.Batch{
		ID:        uuid.NewString(),
		CreatedAt: time.Now().UTC(),
		Words:     words,
	}
	if err := h.Store.SaveBatch(r.Context(), batch); err != nil {
		log.Printf("%s %s: %v", r.Method, r.URL.Path, err)
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusCreated, createBatchResponse{ID: batch.ID, CreatedAt: batch.CreatedAt, Count: len(words)})
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
