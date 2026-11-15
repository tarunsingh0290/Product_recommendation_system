const base = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export async function getRecommendations(occasion, top_k) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 360000);
  try {
    const response = await fetch(`${base}/api/recommendations`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ occasion, top_k }), signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      if (response.status === 429) {
        const wait = data.retry_after_seconds;
        throw new Error(`${data.detail || 'The gift service is busy.'}${wait ? ` Try again in ${wait} seconds.` : ' Please try again shortly.'}`);
      }
      const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join('. ') : data.detail;
      throw new Error(detail || 'Recommendations are temporarily unavailable.');
    }
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('This search took too long. Please try again.');
    if (error instanceof TypeError) throw new Error('Unable to reach the gift service. Check that the backend is running.');
    throw error;
  } finally { clearTimeout(timer); }
}


export async function getProductDetails(productId, signal) {
  try {
    const response = await fetch(`${base}/api/products/${encodeURIComponent(productId)}`, { signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Unable to load this product.');
    return data;
  } catch (error) {
    if (error instanceof TypeError) throw new Error('Unable to reach the product service. Please try again.');
    throw error;
  }
}
