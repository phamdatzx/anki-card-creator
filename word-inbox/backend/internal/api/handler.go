package api

import (
	"encoding/json"
	"errors"
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

type createRequest struct {
	Input string `json:"input"`
	Type  string `json:"type"`
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
	case r.Method == http.MethodGet && path == "/words":
		h.listWords(w, r)
	case r.Method == http.MethodPost && path == "/words":
		h.createWord(w, r)
	case r.Method == http.MethodDelete && strings.HasPrefix(path, "/words/"):
		h.deleteWord(w, r, strings.TrimPrefix(path, "/words/"))
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
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
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

func (h *Handler) listWords(w http.ResponseWriter, r *http.Request) {
	if !auth.RequireBearer(r) {
		writeJSON(w, http.StatusUnauthorized, errorResponse{Error: "unauthorized"})
		return
	}
	words, err := h.Store.List(r.Context())
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"words": words})
}

func (h *Handler) createWord(w http.ResponseWriter, r *http.Request) {
	if !auth.RequireBearer(r) {
		writeJSON(w, http.StatusUnauthorized, errorResponse{Error: "unauthorized"})
		return
	}
	var req createRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid JSON body"})
		return
	}
	input := strings.TrimSpace(req.Input)
	wordType := strings.TrimSpace(req.Type)
	if wordType == "" {
		wordType = model.TypeNormal
	}
	if input == "" {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "input is required"})
		return
	}
	if !model.ValidType(wordType) {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid type"})
		return
	}
	word := model.Word{
		ID:        uuid.NewString(),
		Input:     input,
		Type:      wordType,
		CreatedAt: time.Now().UTC(),
		SyncedAt:  nil,
	}
	created, err := h.Store.Create(r.Context(), word)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: err.Error()})
		return
	}
	writeJSON(w, http.StatusCreated, created)
}

func (h *Handler) deleteWord(w http.ResponseWriter, r *http.Request, id string) {
	if !auth.RequireBearer(r) {
		writeJSON(w, http.StatusUnauthorized, errorResponse{Error: "unauthorized"})
		return
	}
	id = strings.TrimSpace(id)
	if id == "" {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "id is required"})
		return
	}
	if err := h.Store.Delete(r.Context(), id); err != nil {
		if errors.Is(err, store.ErrNotFound) {
			writeJSON(w, http.StatusNotFound, errorResponse{Error: "not found"})
			return
		}
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: err.Error()})
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
