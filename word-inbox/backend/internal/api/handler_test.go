package api_test

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/datjax/vip-translate/word-inbox/backend/internal/api"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
)

func setup(t *testing.T) (*api.Handler, *store.MemoryStore) {
	t.Helper()
	t.Setenv("APP_PASSWORD", "secret")
	t.Setenv("APP_TOKEN", "tok")
	t.Setenv("CORS_ORIGIN", "*")
	mem := store.NewMemoryStore()
	return &api.Handler{Store: mem}, mem
}

func do(h http.Handler, method, path, body, token string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, bytes.NewBufferString(body))
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec
}

func TestLogin(t *testing.T) {
	h, _ := setup(t)

	rec := do(h, http.MethodPost, "/login", `{"password":"secret"}`, "")
	if rec.Code != http.StatusOK {
		t.Fatalf("login status = %d body=%s", rec.Code, rec.Body.String())
	}
	var resp map[string]string
	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	if resp["token"] != "tok" {
		t.Fatalf("token = %q", resp["token"])
	}

	if rec := do(h, http.MethodPost, "/login", `{"password":"nope"}`, ""); rec.Code != http.StatusUnauthorized {
		t.Fatalf("bad login status = %d", rec.Code)
	}
}

func TestCreateBatch(t *testing.T) {
	h, mem := setup(t)

	body := `{"words":[{"input":" test ","type":"normal"},{"input":"make a decision","type":"word_pattern"},{"input":"neat"}]}`
	rec := do(h, http.MethodPost, "/words", body, "tok")
	if rec.Code != http.StatusCreated {
		t.Fatalf("create status = %d body=%s", rec.Code, rec.Body.String())
	}
	var resp struct {
		ID    string `json:"id"`
		Count int    `json:"count"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	if resp.ID == "" || resp.Count != 3 {
		t.Fatalf("response = %+v", resp)
	}

	if len(mem.Batches) != 1 {
		t.Fatalf("stored batches = %d", len(mem.Batches))
	}
	got := mem.Batches[0]
	if got.ID != resp.ID || len(got.Words) != 3 {
		t.Fatalf("stored batch = %+v", got)
	}
	if got.Words[0].Input != "test" {
		t.Fatalf("input not trimmed: %q", got.Words[0].Input)
	}
	if got.Words[2].Type != "normal" {
		t.Fatalf("default type = %q", got.Words[2].Type)
	}
}

func TestCreateBatchRejects(t *testing.T) {
	h, mem := setup(t)

	tooMany := `{"words":[` + strings.TrimSuffix(strings.Repeat(`{"input":"x"},`, api.MaxBatchSize+1), ",") + `]}`
	cases := []struct {
		name   string
		body   string
		token  string
		status int
	}{
		{"unauthorized", `{"words":[{"input":"x"}]}`, "", http.StatusUnauthorized},
		{"invalid json", `{`, "tok", http.StatusBadRequest},
		{"empty batch", `{"words":[]}`, "tok", http.StatusBadRequest},
		{"empty input", `{"words":[{"input":"ok"},{"input":"  "}]}`, "tok", http.StatusBadRequest},
		{"bad type", `{"words":[{"input":"x","type":"nope"}]}`, "tok", http.StatusBadRequest},
		{"too many", tooMany, "tok", http.StatusBadRequest},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if rec := do(h, http.MethodPost, "/words", tc.body, tc.token); rec.Code != tc.status {
				t.Fatalf("status = %d, want %d body=%s", rec.Code, tc.status, rec.Body.String())
			}
		})
	}
	if len(mem.Batches) != 0 {
		t.Fatalf("rejected requests stored %d batches", len(mem.Batches))
	}
}

func TestRemovedRoutes(t *testing.T) {
	h, _ := setup(t)
	for _, method := range []string{http.MethodGet, http.MethodDelete} {
		path := "/words"
		if method == http.MethodDelete {
			path = fmt.Sprintf("/words/%s", "some-id")
		}
		if rec := do(h, method, path, "", "tok"); rec.Code != http.StatusNotFound {
			t.Fatalf("%s %s status = %d", method, path, rec.Code)
		}
	}
}
