package auth

import (
	"crypto/subtle"
	"net/http"
	"os"
	"strings"
)

func Password() string {
	return os.Getenv("APP_PASSWORD")
}

func Token() string {
	return os.Getenv("APP_TOKEN")
}

func CheckPassword(password string) bool {
	expected := Password()
	if expected == "" {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(password), []byte(expected)) == 1
}

func CheckToken(token string) bool {
	expected := Token()
	if expected == "" {
		return false
	}
	return subtle.ConstantTimeCompare([]byte(token), []byte(expected)) == 1
}

func BearerToken(r *http.Request) string {
	header := r.Header.Get("Authorization")
	if header == "" {
		return ""
	}
	const prefix = "Bearer "
	if !strings.HasPrefix(header, prefix) {
		return ""
	}
	return strings.TrimSpace(strings.TrimPrefix(header, prefix))
}

func RequireBearer(r *http.Request) bool {
	return CheckToken(BearerToken(r))
}
