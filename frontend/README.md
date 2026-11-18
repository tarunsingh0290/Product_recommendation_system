# Giftly frontend — complete source

This is a complete React/Vite app with Home, All Items, Gift Suggestions, How It Works, About, and Product Details. Includes a single global stylesheet: `src/styles.css` imported in `src/main.jsx`.

## Install

1. Extract into `occasion-gift-recommender` so that `frontend/package.json` exists. Keep your existing `backend` unchanged.
2. In PowerShell from `frontend`:

```powershell
npm install
Copy-Item .env.example .env
npm run build
npm run dev
```

3. Start your FastAPI server separately. `frontend/.env` should contain `VITE_API_BASE_URL=http://127.0.0.1:8000`.

## API contracts

- `GET /api/products/`: product array or object with `products`, `items`, `results`, or `data`. Full catalog is displayed with 8-item **client-side** pagination. If backend advertises `total_pages`, pages 2+ are fetched with `page` and `limit` parameters.
- `GET /api/products/{product_id}`: detailed product; falls back to catalog entry.
- `POST /api/v1/recommendations`: occasion and top_k=10. **Actual number displayed is whatever the backend returns**, up to ten. The UI does not invent recommendations.

The frontend uses catalog data to enrich sparse recommendation responses with brand, descriptions, and discounts. The provided `products.json` has `price` (original) and `discountPercentage`, so the discount is calculated from those fields if returned by the backend. Missing discounts remain missing. Product photos depend on reachable `mainImage` URLs; broken links display a neutral fallback.

## Files

```text
frontend/
  .env.example
  index.html
  package.json
  vite.config.js
  public/images/
  src/main.jsx
  src/App.jsx
  src/styles.css
  src/components/{Navbar,OccasionSearch,ProductCard,StatePanel}.jsx
  src/pages/{Home,AllItems,Suggestions,HowItWorks,About,ProductDetails}.jsx
  src/services/api.js
  src/utils/pricing.js
```

## Note on product data

If Swagger `/api/products/` does not return discountPercentage, add that field to your backend catalog response. The frontend does not read the local JSON directly. Verify total returned and image URLs at `http://127.0.0.1:8000/api/products/`.
