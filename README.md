# Gemini Product Search Stack

This repository contains an end-to-end example of a product catalogue search
pipeline that combines:

- **CRUD + REST API** (`FastAPI`) backed by PostgreSQL.
- **ETL worker** that reacts to CRUD events, chunks product text, generates
  embeddings with `models/text-embedding-004`, and stores vectors in OpenSearch.
- **OpenSearch** for vector similarity search.
- **MinIO** (S3-compatible) for storing product images.
- **Vue frontend** to manage products and run semantic search.

All components run locally via `docker-compose`.

---

## Architecture Overview

1. **API service (`backend/api`)**
   - Exposes CRUD endpoints for products (id, name, description, images).
   - Persists data in PostgreSQL via SQLAlchemy.
   - Emits embedding jobs into `embedding_jobs` table on every create/update/delete.
   - Provides `/search` endpoint that embeds the query text and performs a KNN
     lookup against OpenSearch.
   - Offers `/uploads/presign` to generate pre-signed MinIO upload URLs.

2. **ETL worker (`backend/etl`)**
   - Polls the `embedding_jobs` table using `SELECT ... FOR UPDATE SKIP LOCKED`.
   - On *upsert* jobs: loads the product, chunks its content, calls Gemini
     embeddings (`embed_content`), and indexes vectors into OpenSearch.
   - On *delete* jobs: removes existing vectors from OpenSearch.

3. **OpenSearch**
   - Stores product chunks as documents with a `knn_vector` field.
   - Supports approximate cosine similarity search for semantic queries.

4. **MinIO**
   - Acts as an S3-compatible image store for product assets.

5. **Vue Frontend (`frontend`)**
   - Simple dashboard to create/update/delete products and run semantic search.
   - Communicates with the API service (`VITE_API_BASE_URL`).

---

## Prerequisites

- Docker & Docker Compose.
- A Google Gemini API key with access to `models/text-embedding-004`
  (set `GEMINI_API_KEY` in your shell or `.env`).
- (Optional) Node.js ≥ 20 if you want to run the frontend outside Docker.

---

## Getting Started

1. **Create an environment file (optional but recommended):**

   ```bash
   cat <<'EOF' > .env
   GEMINI_API_KEY=your_api_key_here
   DATABASE_URL=postgresql+psycopg://app:app@postgres:5432/app
   OPENSEARCH_HOSTS=["https://opensearch:9200"]
   OPENSEARCH_INDEX=products
   OPENSEARCH_INITIAL_ADMIN_PASSWORD=Opensearch#2025!
   OPENSEARCH_USERNAME=admin
   OPENSEARCH_PASSWORD=Opensearch#2025!
   MINIO_ENDPOINT=minio:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_BUCKET=product-images
   MINIO_SECURE=false
   EMBEDDING_MODEL=models/text-embedding-004
   CHUNK_SIZE=400
   CHUNK_OVERLAP=50
   EOF
   ```

2. **Launch the stack:**

   ```bash
   export GEMINI_API_KEY=your_api_key  # or rely on .env via docker compose
   docker compose up -d --build
   ```

   Services will come online on:

   - API: `http://localhost:8000`
   - Frontend: `http://localhost:5173`
   - OpenSearch: `https://localhost:9200` (user `admin`, password from `.env`)
   - MinIO console: `http://localhost:9001` (user/pass `minioadmin`)

3. **Interact with the system:**

   - Navigate to the frontend and add products.
   - Alternatively, call the API directly:

     ```bash
     curl -X POST http://localhost:8000/products/ \
       -H "Content-Type: application/json" \
       -d '{
         "name": "Google Pixel 9",
         "description": "Flagship Android phone with Gemini features",
         "images": ["https://example.com/pixel9.jpg"]
       }'
     ```

   - Within a few seconds the ETL worker will embed the product description,
     index it into OpenSearch, and subsequent searches will surface the item.

4. **Shutdown:**

   ```bash
   docker compose down
   ```

---

## API Highlights

| Method | Path                    | Description                                  |
| ------ | ----------------------- | -------------------------------------------- |
| GET    | `/products/`            | List products                                |
| POST   | `/products/`            | Create a product (triggers embedding job)    |
| PUT    | `/products/{id}`        | Update a product (re-triggers embedding job) |
| DELETE | `/products/{id}`        | Delete product & vectors                     |
| GET    | `/search/?q=...`        | Semantic search via Gemini embeddings + KNN  |
| GET    | `/uploads/presign?filename=...` | Generate MinIO pre-signed upload URL |

All JSON payloads follow the Pydantic schemas under `backend/api/app/schemas.py`.

---

## Worker Behaviour

- **Chunking:** naive word-based chunker (configurable size & overlap).
- **Embeddings:** `google-genai` SDK with `models/text-embedding-004`.
- **Retry strategy:** Tenacity-based exponential backoff (both API and ETL).
- **Idempotency:** each product job replaces existing vectors before indexing.
- **Failure handling:** jobs re-queued up to `MAX_JOB_ATTEMPTS` then marked failed.

Tune worker behaviour via environment variables (`CHUNK_SIZE`, `CHUNK_OVERLAP`,
`POLL_INTERVAL_SECONDS`, `MAX_JOB_ATTEMPTS`).

---

## Frontend Notes

- Vite + Vue 3 single-page dashboard.
- `VITE_API_BASE_URL` defaults to `http://localhost:8000` in Docker. Override via
  `.env` or environment variables if needed.
- For local development outside Docker:

  ```bash
  cd frontend
  npm install
  npm run dev
  ```

---

## Development Tips

- The API auto-creates PostgreSQL tables on startup (`Base.metadata.create_all`).
- Ensure `google-genai>=0.3.0`; older versions lack File Search & embedding APIs.
- OpenSearch index creation happens lazily on first embedding (dimension inferred
  from Gemini output).
- MinIO buckets are created on demand when requesting upload URLs.
- Check the ETL logs (`docker compose logs etl -f`) if vectors are not appearing.

---

## Future Improvements

- Swap the naive chunker for an LLM-aware chunker (e.g. token windowing).
- Persist embedding dimensionality to avoid re-inferring on every job.
- Add background tasks or streaming updates to the frontend.
- Harden auth (JWT) and multi-tenant storage.
