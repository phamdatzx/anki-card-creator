package api_test

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/datjax/vip-translate/word-inbox/backend/internal/api"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/store"
)

func TestLoginAndCRUD(t *testing.T) {
	t.Setenv("APP_PASSWORD", "secret")
	t.Setenv("APP_TOKEN", "tok")
	t.Setenv("CORS_ORIGIN", "*")

	h := &api.Handler{Store: store.NewMemoryStore()}

	loginBody := bytes.NewBufferString(`{"password":"secret"}`)
	loginReq := httptest.NewRequest(http.MethodPost, "/login", loginBody)
	loginRec := httptest.NewRecorder()
	h.ServeHTTP(loginRec, loginReq)
	if loginRec.Code != http.StatusOK {
		t.Fatalf("login status = %d body=%s", loginRec.Code, loginRec.Body.String())
	}
	var loginResp map[string]string
	if err := json.Unmarshal(loginRec.Body.Bytes(), &loginResp); err != nil {
		t.Fatal(err)
	}
	if loginResp["token"] != "tok" {
		t.Fatalf("token = %q", loginResp["token"])
	}

	badLogin := httptest.NewRequest(http.MethodPost, "/login", bytes.NewBufferString(`{"password":"nope"}`))
	badRec := httptest.NewRecorder()
	h.ServeHTTP(badRec, badLogin)
	if badRec.Code != http.StatusUnauthorized {
		t.Fatalf("bad login status = %d", badRec.Code)
	}

	createReq := httptest.NewRequest(http.MethodPost, "/words", bytes.NewBufferString(`{"input":"test","type":"normal"}`))
	createReq.Header.Set("Authorization", "Bearer tok")
	createRec := httptest.NewRecorder()
	h.ServeHTTP(createRec, createReq)
	if createRec.Code != http.StatusCreated {
		t.Fatalf("create status = %d body=%s", createRec.Code, createRec.Body.String())
	}
	var created map[string]any
	if err := json.Unmarshal(createRec.Body.Bytes(), &created); err != nil {
		t.Fatal(err)
	}
	id, _ := created["id"].(string)
	if id == "" {
		t.Fatal("missing id")
	}

	emptyReq := httptest.NewRequest(http.MethodPost, "/words", bytes.NewBufferString(`{"input":"","type":"normal"}`))
	emptyReq.Header.Set("Authorization", "Bearer tok")
	emptyRec := httptest.NewRecorder()
	h.ServeHTTP(emptyRec, emptyReq)
	if emptyRec.Code != http.StatusBadRequest {
		t.Fatalf("empty input status = %d", emptyRec.Code)
	}

	badType := httptest.NewRequest(http.MethodPost, "/words", bytes.NewBufferString(`{"input":"x","type":"nope"}`))
	badType.Header.Set("Authorization", "Bearer tok")
	badTypeRec := httptest.NewRecorder()
	h.ServeHTTP(badTypeRec, badType)
	if badTypeRec.Code != http.StatusBadRequest {
		t.Fatalf("bad type status = %d", badTypeRec.Code)
	}

	listReq := httptest.NewRequest(http.MethodGet, "/words", nil)
	listReq.Header.Set("Authorization", "Bearer tok")
	listRec := httptest.NewRecorder()
	h.ServeHTTP(listRec, listReq)
	if listRec.Code != http.StatusOK {
		t.Fatalf("list status = %d", listRec.Code)
	}

	unauth := httptest.NewRequest(http.MethodGet, "/words", nil)
	unauthRec := httptest.NewRecorder()
	h.ServeHTTP(unauthRec, unauth)
	if unauthRec.Code != http.StatusUnauthorized {
		t.Fatalf("unauth status = %d", unauthRec.Code)
	}

	delReq := httptest.NewRequest(http.MethodDelete, "/words/"+id, nil)
	delReq.Header.Set("Authorization", "Bearer tok")
	delRec := httptest.NewRecorder()
	h.ServeHTTP(delRec, delReq)
	if delRec.Code != http.StatusNoContent {
		t.Fatalf("delete status = %d body=%s", delRec.Code, delRec.Body.String())
	}
}
