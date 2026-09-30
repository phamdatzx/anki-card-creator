package store

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"sync"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/aws/aws-sdk-go-v2/service/s3/types"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/model"
)

var ErrNotFound = errors.New("word not found")
var ErrConflict = errors.New("concurrent update conflict")

type Store interface {
	List(ctx context.Context) ([]model.Word, error)
	Create(ctx context.Context, word model.Word) (model.Word, error)
	Delete(ctx context.Context, id string) error
}

type S3Store struct {
	client *s3.Client
	bucket string
	key    string
	mu     sync.Mutex
}

func NewS3Store(ctx context.Context) (*S3Store, error) {
	bucket := os.Getenv("S3_BUCKET")
	if bucket == "" {
		return nil, fmt.Errorf("S3_BUCKET is required")
	}
	key := os.Getenv("S3_KEY")
	if key == "" {
		key = "words.json"
	}
	cfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, fmt.Errorf("load aws config: %w", err)
	}
	// S3_ENDPOINT points the client at a local emulator (e.g. LocalStack).
	endpoint := os.Getenv("S3_ENDPOINT")
	client := s3.NewFromConfig(cfg, func(o *s3.Options) {
		if endpoint != "" {
			o.BaseEndpoint = aws.String(endpoint)
			o.UsePathStyle = true
		}
	})
	return &S3Store{
		client: client,
		bucket: bucket,
		key:    key,
	}, nil
}

func (s *S3Store) List(ctx context.Context) ([]model.Word, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	doc, _, err := s.read(ctx)
	if err != nil {
		return nil, err
	}
	return sortNewestFirst(doc.Words), nil
}

func (s *S3Store) Create(ctx context.Context, word model.Word) (model.Word, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	for attempt := 0; attempt < 3; attempt++ {
		doc, etag, err := s.read(ctx)
		if err != nil {
			return model.Word{}, err
		}
		doc.Words = append(doc.Words, word)
		if err := s.write(ctx, doc, etag); err != nil {
			if errors.Is(err, ErrConflict) {
				continue
			}
			return model.Word{}, err
		}
		return word, nil
	}
	return model.Word{}, ErrConflict
}

func (s *S3Store) Delete(ctx context.Context, id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	for attempt := 0; attempt < 3; attempt++ {
		doc, etag, err := s.read(ctx)
		if err != nil {
			return err
		}
		next := make([]model.Word, 0, len(doc.Words))
		found := false
		for _, w := range doc.Words {
			if w.ID == id {
				found = true
				continue
			}
			next = append(next, w)
		}
		if !found {
			return ErrNotFound
		}
		doc.Words = next
		if err := s.write(ctx, doc, etag); err != nil {
			if errors.Is(err, ErrConflict) {
				continue
			}
			return err
		}
		return nil
	}
	return ErrConflict
}

func (s *S3Store) read(ctx context.Context) (model.Store, *string, error) {
	out, err := s.client.GetObject(ctx, &s3.GetObjectInput{
		Bucket: aws.String(s.bucket),
		Key:    aws.String(s.key),
	})
	if err != nil {
		var nsk *types.NoSuchKey
		var nsf *types.NotFound
		if errors.As(err, &nsk) || errors.As(err, &nsf) {
			return model.Store{Words: []model.Word{}}, nil, nil
		}
		// Some SDKs wrap missing keys differently.
		var apiErr interface{ ErrorCode() string }
		if errors.As(err, &apiErr) && (apiErr.ErrorCode() == "NoSuchKey" || apiErr.ErrorCode() == "NotFound") {
			return model.Store{Words: []model.Word{}}, nil, nil
		}
		return model.Store{}, nil, fmt.Errorf("get s3 object: %w", err)
	}
	defer out.Body.Close()
	body, err := io.ReadAll(out.Body)
	if err != nil {
		return model.Store{}, nil, fmt.Errorf("read s3 body: %w", err)
	}
	if len(bytes.TrimSpace(body)) == 0 {
		return model.Store{Words: []model.Word{}}, out.ETag, nil
	}
	var doc model.Store
	if err := json.Unmarshal(body, &doc); err != nil {
		return model.Store{}, nil, fmt.Errorf("decode words.json: %w", err)
	}
	if doc.Words == nil {
		doc.Words = []model.Word{}
	}
	return doc, out.ETag, nil
}

func (s *S3Store) write(ctx context.Context, doc model.Store, etag *string) error {
	payload, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return fmt.Errorf("encode words.json: %w", err)
	}
	input := &s3.PutObjectInput{
		Bucket:      aws.String(s.bucket),
		Key:         aws.String(s.key),
		Body:        bytes.NewReader(payload),
		ContentType: aws.String("application/json"),
	}
	if etag != nil && *etag != "" {
		input.IfMatch = etag
	}
	_, err = s.client.PutObject(ctx, input)
	if err != nil {
		var apiErr interface{ ErrorCode() string }
		if errors.As(err, &apiErr) && apiErr.ErrorCode() == "PreconditionFailed" {
			return ErrConflict
		}
		return fmt.Errorf("put s3 object: %w", err)
	}
	return nil
}

func sortNewestFirst(words []model.Word) []model.Word {
	out := make([]model.Word, len(words))
	copy(out, words)
	sort.Slice(out, func(i, j int) bool {
		return out[i].CreatedAt.After(out[j].CreatedAt)
	})
	return out
}

// MemoryStore is used for local development without AWS.
type MemoryStore struct {
	mu    sync.Mutex
	words []model.Word
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{words: []model.Word{}}
}

func (m *MemoryStore) List(ctx context.Context) ([]model.Word, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	return sortNewestFirst(m.words), nil
}

func (m *MemoryStore) Create(ctx context.Context, word model.Word) (model.Word, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.words = append(m.words, word)
	return word, nil
}

func (m *MemoryStore) Delete(ctx context.Context, id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	next := make([]model.Word, 0, len(m.words))
	found := false
	for _, w := range m.words {
		if w.ID == id {
			found = true
			continue
		}
		next = append(next, w)
	}
	if !found {
		return ErrNotFound
	}
	m.words = next
	return nil
}
