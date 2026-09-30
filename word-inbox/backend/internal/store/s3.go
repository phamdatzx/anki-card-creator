package store

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"sync"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/datjax/vip-translate/word-inbox/backend/internal/model"
)

type Store interface {
	SaveBatch(ctx context.Context, batch model.Batch) error
}

// S3Store writes each batch to its own object: <prefix><createdAt>-<id>.json.
type S3Store struct {
	client *s3.Client
	bucket string
	prefix string
}

func NewS3Store(ctx context.Context) (*S3Store, error) {
	bucket := os.Getenv("S3_BUCKET")
	if bucket == "" {
		return nil, fmt.Errorf("S3_BUCKET is required")
	}
	prefix := os.Getenv("S3_PREFIX")
	if prefix == "" {
		prefix = "batches/"
	}
	if !strings.HasSuffix(prefix, "/") {
		prefix += "/"
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
	return &S3Store{client: client, bucket: bucket, prefix: prefix}, nil
}

func (s *S3Store) SaveBatch(ctx context.Context, batch model.Batch) error {
	payload, err := json.MarshalIndent(batch, "", "  ")
	if err != nil {
		return fmt.Errorf("encode batch: %w", err)
	}
	key := BatchKey(s.prefix, batch)
	_, err = s.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket:      aws.String(s.bucket),
		Key:         aws.String(key),
		Body:        bytes.NewReader(payload),
		ContentType: aws.String("application/json"),
		IfNoneMatch: aws.String("*"),
	})
	if err != nil {
		return fmt.Errorf("put s3 object %s: %w", key, err)
	}
	return nil
}

// BatchKey sorts chronologically: batches/20260930T060000Z-<id>.json.
func BatchKey(prefix string, batch model.Batch) string {
	return fmt.Sprintf("%s%s-%s.json", prefix, batch.CreatedAt.UTC().Format("20060102T150405Z"), batch.ID)
}

// MemoryStore is used for local development and tests without AWS.
type MemoryStore struct {
	mu      sync.Mutex
	Batches []model.Batch
}

func NewMemoryStore() *MemoryStore {
	return &MemoryStore{Batches: []model.Batch{}}
}

func (m *MemoryStore) SaveBatch(ctx context.Context, batch model.Batch) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.Batches = append(m.Batches, batch)
	return nil
}
