# Flow 
You send the request -> it carries the occasion and hits the API -> the GROQ api key is hit -> occasion is sent to the LLM model to convert the occasion into a context -> the context is then converted to Embeddings -> the products description is also converted to vector embeddings -> then we run the cosine similarity test to get the similarity score -> top 10 products stored in a list -> then the list is thrown to the LLM model to test whether the result is appropriate or not -> the result is displayed to the user.

# Project Recommendation System

A local React + FastAPI application that retrieves catalog products with MiniLM embeddings, then uses Groq to validate their suitability. It returns at most the requested number of products; every returned ID is resolved from the eligible backend catalog.

## Setup on Windows

Run these commands from this repository in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

Set `GROQ_API_KEY` in `backend/.env`. One key handles both occasion context generation and suitability validation. Never put it in frontend configuration. The default model is `openai/gpt-oss-20b`; strict structured-output support is verified for this model and `openai/gpt-oss-120b` according to [Groq documentation](https://console.groq.com/docs/structured-outputs). Other models fail closed until their structured-output support is reviewed.

Build the offline index, then start FastAPI:

```powershell
.\.venv\Scripts\python.exe backend/scripts/build_index.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

The first index build can download the embedding model. Later loads prefer the local model cache. Product embeddings are generated only by the index script. An API request embeds only its occasion query.

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite forwards `/api` to FastAPI at `127.0.0.1:8000`. Swagger is at `http://127.0.0.1:8000/docs`. For a separate production frontend origin, set backend `CORS_ORIGINS` and frontend `VITE_API_URL`, then run `npm run build`. The Python backend requires separate hosting; this repository has not been deployed.

## Catalog and index

`backend/data/products.json` is an unchanged copy of the supplied catalog: 110 rows, 104 currently eligible. The adapter validates the observed export fields: `id`, `name`, `brand`, `description`, `shortDescription`, `mainImage`, `price`, `stock`, `isApproved`, `status`, `deletedAt`, and `productGroupId`. Other export fields are retained in the JSON but omitted from retrieval. Duplicate IDs or malformed trusted fields fail loading.

A product is eligible only when `status == "ACTIVE"`, `isApproved == true`, `stock > 0`, and `deletedAt == null`. Eligibility fields must be present; unknown statuses fail closed. Numeric price strings are parsed; missing prices remain absent. The source has category IDs but no category labels, and no currency field. The UI displays no invented category or currency symbol. Prices reflect the supplied `price` field without inferred discounts or taxes.

Search text combines available name, brand, short description, and full description. The index contains normalized 384-dimensional float32 vectors, sorted stable product IDs, and a manifest with catalog/model/configuration metadata and file checksums. Startup verifies alignment, dimensions, finite values, normalization, and checksums. A catalog file metadata change blocks requests, including cache hits; rebuild and restart after edits. This avoids rereading the entire catalog per request. Catalog files must be managed by trusted operators; file-stat checks are not a tamper-proof filesystem monitor.

## Recommendation policy

1. Validate the request; load the already initialized eligible catalog/index.
2. Get structured occasion context from Groq, or reuse a bounded TTL context cache.
3. Embed the context and sort cosine results by score descending, ID ascending.
4. Send the first 20 candidates in one suitability request. Validate the complete ID set and all scores; missing, duplicate, or unknown IDs invalidate the batch.
5. Recheck eligibility and apply the experimental suitability threshold of 0.70.
6. Rank by suitability descending, cosine descending, then ID ascending. No unvalidated weighted coefficients are used.
7. Deduplicate by existing `productGroupId`; use normalized name plus brand when a group is absent. Keep the highest ranked member.
8. If fewer than `top_k` survive, validate the next non-overlapping batch. Stop after two validation batches and return the best available results.

The server refuses to serve unvalidated recommendations when Groq fails. Each LLM operation has at most three HTTP attempts, a configurable timeout, and a bounded retry for network failures, HTTP 429, and provider 5xx errors. HTTP retries honor numeric Retry-After delays up to 60 seconds; longer delays return immediately rather than retrying too early. Malformed JSON, schema errors, partial evaluations, and other nontransient HTTP errors return a sanitized 502. Groq rate limits return 429, and rejected credentials/access return 503. Missing credentials/index/catalog return 503. Input validation returns 422. No provider-supplied product metadata is used in response cards. Product metadata is treated as untrusted prompt data.

Occasion policy: accept a trimmed string of 2â€“100 characters with at least two letters. Groq must also classify it as a meaningful gifting occasion; nonsense, unrelated requests, and instruction attacks are rejected with 422. Arbitrary descriptions are supported rather than restricting users to a fixed occasion list. This semantic gate depends on provider accuracy; the structural ID and eligibility checks remain deterministic.

Successful response caches, occasion-context caches, and validated-batch caches are process-local, thread-safe, capped at 128 entries each, and expire after one hour by default. Concurrent identical cache misses can make duplicate provider calls. Caches are not shared between worker processes. The API logs aggregate latency, provider attempts, and provider-reported token usage without keys or prompt content. Token usage unavailable after a provider timeout cannot be measured.

## API

```http
POST /api/recommendations
Content-Type: application/json

{"occasion":"anniversary","top_k":10}
```

The response contains `occasion`, `requested_count`, `returned_count`, `status` (`ok`, `no_results`, or `partial`), and flat `recommendations` containing catalog metadata, `similarity_score`, `suitability_score`, and `reason`. Timing, cache status, LLM attempts, and token counts are included for measurement. Scores are ranking signals, not calibrated probabilities. A cached response reports zero new provider attempts/tokens.

`GET /api/health` reports process liveness and initialization state. `GET /api/health/ready` returns 503 when setup is missing or the catalog changed; it does not spend tokens probing Groq. Unknown request fields and coerced/noninteger counts are rejected. Maximum `top_k` is 10.

## Configuration

See `backend/.env.example`. Paths resolve relative to `backend`, independent of the working directory.

| Variable | Default / purpose |
|---|---|
| `GROQ_API_KEY` | Required for recommendations |
| `GROQ_MODEL` | `openai/gpt-oss-20b` |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2`; other models rejected by this index version |
| `DEFAULT_TOP_K`, `MAX_TOP_K` | 10, 10; each constrained to 1â€“10 |
| `CANDIDATE_BATCH_SIZE` | 20; configurable from 20 to 30 |
| `MAX_VALIDATION_BATCHES` | 2; constrained to 1â€“2 |
| `LLM_TEMPERATURE` | 0.1 |
| `LLM_TIMEOUT_SECONDS` | 15 per HTTP attempt |
| `LLM_MAX_RETRY_WAIT_SECONDS` | 60; total reset-wait budget per LLM operation across retries |
| `LLM_MAX_HTTP_ATTEMPTS` | 3; bounded from 1 to 3 attempts per operation |
| `SUITABILITY_THRESHOLD` | 0.70; experimental, tune with human labels |
| `SIMILARITY_MINIMUM` | Unset; no arbitrary prefilter |
| `CACHE_TTL_SECONDS` | 3600 |
| `CORS_ORIGINS` | `http://localhost:5173`; comma-separated string or JSON array |
| `CATALOG_PATH`, `ARTIFACTS_PATH` | `data/products.json`, `artifacts` |

The browser timeout is 360 seconds to allow the worst-case bounded HTTP attempts and reset delays; the provisional p95 target of eight seconds has not been demonstrated. This MVP has no public authentication or inbound rate limiter; deploy behind suitable access controls if exposing it beyond trusted local development.

## Tests and evaluation

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests -c backend/pytest.ini
cd frontend
npm run build
```

Tests use isolated catalog fixtures, fake normalized vectors, and mocked Groq responses, with no paid calls. They cover five supported occasions, schemas, eligibility, ranking, deduplication, ID membership, retry limits, cache behavior, provider errors, index integrity, API routing, and Swagger. Test fixture products are never added to the application catalog.

For relevance evaluation, have independent human reviewers label every eligible catalog product for each held-out occasion. Keep tuning data in a separate file. Populate `backend/tests/ground_truth.json` with this structure:

```json
{
  "split": "evaluation",
  "occasions": [
    {
      "occasion": "birthday",
      "relevant_product_ids": [],
      "judged_product_ids": []
    }
  ]
}
```

Use real IDs only. The harness requires all eligible IDs in `judged_product_ids` to avoid treating unjudged outputs as negatives. With a configured key and index:

```powershell
cd backend
..\.venv\Scripts\python.exe tests/evaluate_model.py --labels tests/ground_truth.json
```

This makes paid Groq calls and writes `evaluation_results.json`. Baseline A embeds the raw occasion and uses cosine only; System B runs context generation and suitability validation. Reports include Precision@10 (fixed denominator 10), per-occasion precision, success rate (Precision@10 â‰¥ 0.70), invalid-ID rate, duplicate rate, p95 latency, token consumption, and provider failure rate. Each System B occasion uses fresh caches. Models are warmed by baseline retrieval, so p95 excludes process/model startup. Provider failures count as zero precision. Empty labels cause an explicit stop instead of invented metrics.

Independent relevance labels are still missing. Precision, occasion success rate, real-provider failure rate, and end-to-end latency targets have therefore **not** been measured. A live birthday request after configuring the backend key returned 10 catalog recommendations using three HTTP attempts and 5,783 provider-reported tokens; this single request is not a relevance evaluation or latency benchmark. The empty ground-truth file deliberately contains no synthetic relevance judgments.

Verified during this build: 66 backend tests passed; Vite production build succeeded; Python dependency consistency passed; the actual index has shape `(104, 384)` with normalized vectors and catalog-aligned IDs. A live local smoke check passed frontend HTML, Swagger, OpenAPI, health forwarding, recommendation POST forwarding, and missing-key error handling. Temporary servers were stopped afterward. Browser interaction and visual rendering were not tested because no browser automation tool was available. A five-query cosine-only smoke run after model load measured 81.13, 8.09, 10.88, 8.70, and 9.32 ms for birthday, wedding, anniversary, baby shower, and Diwali respectively (sample p95: 67.08 ms). These five local measurements exclude Groq and do not establish relevance or an end-to-end latency target.

The optional local network smoke check starts temporary servers on free ports, sends a recommendation request through Vite, verifies the missing-key error, and stops both servers. It deliberately disables the key for this check:

```powershell
.\.venv\Scripts\python.exe backend/scripts/smoke_local.py
```

## Source layout

```text
backend/
  app/
    main.py                  # FastAPI lifespan, CORS, error translation
    core/                    # Typed environment settings, service errors
    routers/                 # Recommendations, liveness, readiness
    schemas/                 # API and external LLM validation
    models/                  # Internal product, occasion, ranked-product dataclasses
    ai/                      # MiniLM, cosine search, Groq, context, suitability
    services/                # Catalog, index, orchestration, bounded caches
    utils/                   # Text normalization
  data/products.json         # Original supplied export
  artifacts/                # Local vectors, IDs, checksum manifest
  scripts/build_index.py
  tests/                    # Deterministic tests and held-out evaluation harness
frontend/
  src/App.jsx
  src/components/ProductCard.jsx
  src/services/api.js
  src/style.css
```

Created from an empty workspace apart from the existing virtual environment; no existing implementation, BM25 module, or RRF module was available to reuse.

Provider debugging: a live request reproduced HTTP 429 during product validation. Validation payloads now send distinct IDs/names/brands plus at most 350 description characters, ask for short explanations, and use low reasoning effort with separate context and validation completion budgets (1,024 / 3,072 tokens). Provider failure logs include only schema, status, and error type rather than credentials, prompts, or raw responses. Truncated output produces an explicit service error. Account quotas can still limit repeated or concurrent searches.

Frontend follow-up verification: fixed missing React imports in App.jsx and ProductCard.jsx for the classic JSX transform. Server rendering passed for the initial form and product cards; the production build passed. Exact-count fixture checks now cover 1, 7, and 10 results across five occasions. The live Birthday API request returned exactly 10 unique eligible catalog IDs above the suitability threshold in 15,146.57 ms, using three HTTP attempts and 6,449 tokens. Its local response is saved at backend/artifacts/live_verification.json. Batch structured-output schemas now constrain candidate IDs to the submitted enum and require the complete evaluation count; an additional ID-set check still rejects duplicates. This verifies one live occasion, not a guarantee of 10 suitable products for every occasion or an achieved relevance target. Browser visual interaction remains untested.

Consecutive-search handling: provider requests are serialized per backend process (lock acquisition is bounded at five seconds), and numeric Retry-After waits up to 60 seconds are honored automatically. Larger waits return HTTP 429 with Retry-After and retry_after_seconds; the frontend displays the cooldown. Existing validated candidate batches are reused when top_k changes. If the optional second batch fails after the first batch produced suitable products, the response is explicitly partial with a visible warning and only those verified products. Partial responses are not stored in the full-response cache, so a retry can resume using the validated first batch. Initial-batch failures still return an error; no unvalidated products are substituted. Provider daily/token limits and quotas shared with other applications can still prevent requests. These process-local controls cannot remove account-wide limits or coordinate multiple backend workers.

Retry follow-up: Groq was observed returning another 429 even after its first Retry-After delay. Each LLM operation now permits at most three HTTP attempts and at most 60 seconds of total reset waiting, with a one-second buffer after numeric reset delays when the budget permits. The two validation-batch limit is unchanged. The browser timeout is six minutes to accommodate default worst-case bounded attempts and waits. This improves transient quota recovery; it cannot guarantee success under exhausted daily limits or quota consumed by other apps. Run `.\.venv\Scripts\python.exe backend/scripts/check_consecutive_searches.py` from the repository root for a live back-to-back check; this consumes provider quota.

Live consecutive-search verification after the retry fix: Birthday returned HTTP 200 with 10 unique eligible products in 42,915.29 ms (3 HTTP attempts, 6,673 tokens); the immediately following Anniversary request returned HTTP 200 with 10 unique eligible products in 41,247.46 ms (7 HTTP attempts across context and two validation batches, 6,939 tokens). Anniversary automatically recovered from provider 429 responses. Repeated Birthday was served from cache, and requesting five Birthday results used zero new provider attempts. The sanitized report is backend/artifacts/consecutive_search_verification.json. These results do not meet the provisional eight-second latency target and do not measure recommendation precision.
#   P r o d u c t _ r e c o m m e n d a t i o n _ s y s t e m 
 
 

## Product cards and detail pages

Recommendation cards show the catalog brand, main image and price, and link to `#product/<product_id>`. Clicking a card opens a product detail page; browser Back and the back-to-recommendations link preserve the current search results. The detail page fetches `GET /api/products/{product_id}` directly from the eligible catalog without Groq or query embeddings. This endpoint remains available when the catalog loads but recommendation-provider setup is missing.

Details include the name, full description, main image, brand, price, discount directly below the price, and weight. `discountPercentage` is displayed as **Discount offered**: the source does not define a separate maximum negotiable discount. `weight` is preserved as recorded and labeled with **unit not specified**, because the catalog contains no weight-unit field. No currency, weight unit, or additional discount is inferred. Missing images have a placeholder; absent values are explicitly marked as not specified. Unknown or ineligible IDs return 404; catalog changes block stale details. The existing product JSON and embedding text are unchanged, so this presentation change does not require re-embedding.
