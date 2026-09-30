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

// Word is one captured item inside a batch.
type Word struct {
	Input string `json:"input"`
	Type  string `json:"type"`
}

// Batch is one "Send" from the frontend, stored as a single S3 object.
type Batch struct {
	ID        string    `json:"id"`
	CreatedAt time.Time `json:"createdAt"`
	Words     []Word    `json:"words"`
}

func ValidType(t string) bool {
	_, ok := AllowedTypes[t]
	return ok
}
