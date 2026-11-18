const BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, options);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(`Cannot reach FastAPI at ${BASE}. Start the backend and check CORS.`);
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error(`Invalid JSON from API (HTTP ${response.status}).`); }
  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map(item => item.msg || "Validation error").join("; ")
      : typeof data?.detail === "string" ? data.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return data;
}

const first = (...values) => values.find(v => v !== undefined && v !== null && v !== "");

export function normalizeProduct(source = {}, index = 0) {
  const product = source?.product || source || {};
  return {
    ...product,
    product_id: String(first(product.product_id, product.id, product.productId, product._id, `row-${index}`)),
    name: first(product.name, product.title, "Unnamed product"),
    brand: first(product.brand, product.brandName, ""),
    price: first(product.price, product.originalPrice, product.mrp, product.listPrice),
    originalPrice: first(product.originalPrice, product.original_price, product.mrp, product.listPrice, product.price),
    discountedPrice: first(product.discountedPrice, product.discountPrice, product.discounted_price, product.discount_price, product.salePrice, product.sellingPrice),
    discountPercentage: first(product.discountPercentage, product.discount_percentage, product.discountPercent, product.discount_percent),
    discountAmount: first(product.discountAmount, product.discount_amount),
    description: first(product.description, ""),
    shortDescription: first(product.shortDescription, product.short_description, ""),
    mainImage: first(product.mainImage, product.image, product.image_url, product.imageUrl, ""),
    category: first(product.category, product.categoryName, ""),
  };
}

function unpack(response) {
  let data = response;
  for (let depth = 0; depth < 4; depth++) {
    if (Array.isArray(data)) return { items: data, metadata: response };
    for (const key of ["products", "items", "results"]) {
      if (Array.isArray(data?.[key])) return { items: data[key], metadata: data };
    }
    if (Array.isArray(data?.data)) return { items: data.data, metadata: data };
    if (data?.data && typeof data.data === "object") { data = data.data; continue; }
    break;
  }
  throw new Error("Unexpected products API response. Check /api/products/ in Swagger.");
}

// A fresh request per component avoids sharing an aborted Promise under React StrictMode.
// Assumes the API supports page/limit whenever it advertises multiple pages.
export async function getCatalog({ signal } = {}) {
  const firstResponse = await request("/api/products/", { signal });
  const { items, metadata } = unpack(firstResponse);
  const size = items.length || 8;
  const total = Number(first(metadata?.total, metadata?.count, metadata?.pagination?.total, NaN));
  const pages = Number(first(metadata?.total_pages, metadata?.totalPages,
    metadata?.pagination?.total_pages, Number.isFinite(total) && items.length ? Math.ceil(total / items.length) : 1));
  const collected = [...items];
  if (Number.isFinite(pages) && pages > 1) {
    for (let page = 2; page <= Math.min(1000, Math.ceil(pages)); page++) {
      const params = new URLSearchParams({ page: String(page), limit: String(size) });
      const next = await request(`/api/products/?${params}`, { signal });
      collected.push(...unpack(next).items);
    }
  }
  const seen = new Set();
  return collected.map(normalizeProduct).filter(product => {
    if (seen.has(product.product_id)) return false;
    seen.add(product.product_id);
    return true;
  });
}

export async function getProducts({ page = 1, limit = 8, search = "", signal } = {}) {
  const catalog = await getCatalog({ signal });
  const term = search.trim().toLowerCase();
  const filtered = term ? catalog.filter(p =>
    [p.name, p.brand, p.description, p.shortDescription, p.category, p.categoryId]
      .filter(Boolean).join(" ").toLowerCase().includes(term)) : catalog;
  const start = (page - 1) * limit;
  return { products: filtered.slice(start, start + limit), total: filtered.length,
    page, limit, total_pages: Math.ceil(filtered.length / limit) };
}

export async function getProduct(productId, { signal } = {}) {
  const id = encodeURIComponent(String(productId));
  try {
    const response = await request(`/api/products/${id}`, { signal });
    const entry = response?.product ?? response?.data?.product ?? response?.data ?? response;
    return normalizeProduct(entry);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    const catalog = await getCatalog({ signal });
    const found = catalog.find(item => item.product_id === String(productId));
    if (found) return found;
    throw error;
  }
}
export function getProductById(productId, signal) { return getProduct(productId, { signal }); }

export async function getRecommendations(occasion, signal) {
  const data = await request("/api/v1/recommendations", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ occasion: occasion.trim(), top_k: 10 }), signal,
  });
  const results = Array.isArray(data?.recommendations) ? data.recommendations : [];
  let catalog = [];
  try { catalog = await getCatalog({ signal }); }
  catch (error) {
    if (error.name === "AbortError") throw error;
    console.warn("Catalog enrichment unavailable:", error.message);
  }
  const byId = new Map(catalog.map(p => [p.product_id, p]));
  const recommendations = results.map((r, i) => {
    const id = String(first(r.product_id, r.id, r.productId, `row-${i}`));
    // Full catalog first, then only defined recommendation fields; do not overwrite
    // an existing catalog discount with an undefined value.
    const base = byId.get(id) || {};
    const extras = Object.fromEntries(Object.entries(r).filter(([, value]) => value != null && value !== ""));
    return normalizeProduct({ ...base, ...extras, product_id: id }, i);
  });
  return { ...data, recommendations, total_recommendations: recommendations.length };
}
