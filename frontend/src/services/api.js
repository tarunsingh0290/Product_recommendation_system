const BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, options);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Cannot reach FastAPI at " + BASE + ". Start the backend and verify CORS.");
  }
  let data;
  try { data = await response.json(); }
  catch { throw new Error(`Invalid JSON returned (HTTP ${response.status}).`); }
  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
      ? data.detail.map(item => item.msg || "Validation error").join("; ")
      : typeof data?.detail === "string" ? data.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return data;
}

const first = (...values) => values.find(value => value !== undefined && value !== null && value !== "");

// All products and recommendation results go through the same field conversion.
export function normalizeProduct(source = {}, index = 0) {
  const product = source?.product || source;
  const price = first(product.price, product.originalPrice, product.mrp, product.listPrice);
  const discountPercentage = first(product.discountPercentage, product.discount_percentage, product.discountPercent);
  return {
    ...product,
    product_id: String(first(product.product_id, product.id, product.productId, product._id, index)),
    name: first(product.name, product.title, "Unnamed product"),
    price,
    brand: first(product.brand, product.brandName, ""),
    description: first(product.description, ""),
    shortDescription: first(product.shortDescription, product.short_description, ""),
    discountPercentage,
    discountedPrice: first(product.discountedPrice, product.discount_price, product.salePrice),
    discountAmount: first(product.discountAmount, product.discount_amount),
    mainImage: first(product.mainImage, product.image, product.image_url, product.imageUrl, ""),
  };
}

// Works with: [...], {products:[...]}, {items:[...]}, {data:[...]},
// {data:{products:[...]}}, and {results:[...]}.
function unpack(response) {
  let data = response;
  for (let i = 0; i < 3 && !Array.isArray(data); i++) {
    if (Array.isArray(data?.products)) return { items: data.products, metadata: data };
    if (Array.isArray(data?.items)) return { items: data.items, metadata: data };
    if (Array.isArray(data?.results)) return { items: data.results, metadata: data };
    if (Array.isArray(data?.data)) return { items: data.data, metadata: response };
    if (data?.data && typeof data.data === "object") { data = data.data; continue; }
    break;
  }
  if (Array.isArray(data)) return { items: data, metadata: response };
  throw new Error("Products API returned an unsupported structure. Inspect /api/products/ in Swagger.");
}

let catalogPromise;

export async function getCatalog({ signal } = {}) {
  const response = await request("/api/products/", { signal });

  const { items, metadata } = unpack(response);

  console.log("Products API response:", response);
  console.log("Products received:", items.length);

  const totalPages = Number(
    metadata?.total_pages ??
    metadata?.totalPages ??
    1
  );

  const allProducts = [...items];

  if (totalPages > 1) {
    for (let page = 2; page <= totalPages; page++) {
      const query = new URLSearchParams({
        page: String(page),
        limit: String(items.length || 8),
      });

      const nextResponse = await request(
        `/api/products/?${query}`,
        { signal }
      );

      allProducts.push(...unpack(nextResponse).items);
    }
  }

  const seen = new Set();

  return allProducts
    .map(normalizeProduct)
    .filter((product) => {
      if (seen.has(product.product_id)) return false;

      seen.add(product.product_id);
      return true;
    });
}

export async function getProducts({ page = 1, limit = 8, search = "", signal } = {}) {
  const products = await getCatalog({ signal });
  const term = search.trim().toLowerCase();
  const filtered = term ? products.filter(product =>
    [product.name, product.brand, product.shortDescription, product.description,
      product.category, product.categoryName, product.categoryId]
      .filter(Boolean).join(" ").toLowerCase().includes(term)
  ) : products;
  const start = (page - 1) * limit;
  return {
    total: filtered.length, page, limit,
    total_pages: Math.ceil(filtered.length / limit),
    products: filtered.slice(start, start + limit),
  };
}

export async function getProduct(productId, { signal } = {}) {
  const id = encodeURIComponent(String(productId));
  try {
    const response = await request(`/api/products/${id}`, { signal });
    const product = response?.product || response?.data?.product || response?.data || response;
    return normalizeProduct(product);
  } catch(error) {
    if (error.name === "AbortError") throw error;
    // Some APIs only expose details for products currently in the catalog.
    const catalog = await getCatalog({ signal });
    const found = catalog.find(item => item.product_id === String(productId));
    if (found) return found;
    throw error;
  }
}

export async function getRecommendations(occasion, signal) {
  const data = await request("/api/v1/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ occasion: occasion.trim(), top_k: 10 }),
    signal,
  });
  return {
    ...data,
    recommendations: (data.recommendations || []).map(normalizeProduct),
  };
}
