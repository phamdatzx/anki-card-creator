package model

import "time"

const (
	TypeNormal      = "normal"
	TypeWordForm    = "word_form"
	TypeWordPattern = "word_pattern"
	TypeSentence    = "sentence"
	TypeVietnamese  = "vietnamese"
)

var AllowedTypes = map[string]struct{}{
	TypeNormal:      {},
	TypeWordForm:    {},
	TypeWordPattern: {},
	TypeSentence:    {},
	TypeVietnamese:  {},
}

type Word struct {
	ID        string     `json:"id"`
	Input     string     `json:"input"`
	Type      string     `json:"type"`
	CreatedAt time.Time  `json:"createdAt"`
	SyncedAt  *time.Time `json:"syncedAt"`
}

type Store struct {
	Words []Word `json:"words"`
}

func ValidType(t string) bool {
	_, ok := AllowedTypes[t]
	return ok
}
