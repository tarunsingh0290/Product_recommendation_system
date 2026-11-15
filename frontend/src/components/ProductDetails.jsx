import React, { useEffect, useState } from 'react';
import { getProductDetails } from '../services/api';

export function ProductDetailsContent({ product }) {
  const [failedImage, setFailedImage] = useState(false);
  const price = product.price == null ? 'Price not listed' : product.currency
    ? new Intl.NumberFormat(undefined, { style: 'currency', currency: product.currency }).format(product.price)
    : new Intl.NumberFormat().format(product.price);
  return <div className="product-detail-layout">
    <div className="product-detail-image">
      {product.image_url && !failedImage
        ? <img src={product.image_url} alt={product.name} onError={() => setFailedImage(true)} />
        : <div className="detail-image-fallback"><span aria-hidden="true">&#10023;</span><p>Product image not available</p></div>}
    </div>
    <div className="product-detail-copy">
      <p className="eyebrow">{product.brand || 'Brand not specified'}</p>
      <h1>{product.name}</h1>
      <div className="detail-price-group">
        <p className="detail-price"><span>Price</span>{price}</p>
        <p className="detail-discount">{product.discount_percentage == null
          ? 'Discount not specified'
          : `Discount offered: ${new Intl.NumberFormat().format(product.discount_percentage)}%`}</p>
      </div>
      <dl className="product-specs">
        <div><dt>Brand</dt><dd>{product.brand || 'Not specified'}</dd></div>
        <div><dt>Weight</dt><dd>{product.weight == null ? 'Not specified' : `${product.weight} (unit not specified)`}</dd></div>
      </dl>
      <section className="product-description" aria-labelledby="description-title">
        <h2 id="description-title">About this product</h2>
        <p>{product.description || product.short_description || 'A description has not been provided for this product.'}</p>
      </section>
    </div>
  </div>;
}

export default function ProductDetails({ productId }) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 15000);
    setLoading(true); setError(''); setProduct(null);
    getProductDetails(productId, controller.signal)
      .then(data => { if (!controller.signal.aborted) setProduct(data); })
      .catch(error => {
        if (timedOut) setError('Loading this product took too long. Please try again.');
        else if (error.name !== 'AbortError') setError(error.message);
      })
      .finally(() => { clearTimeout(timer); if (!controller.signal.aborted || timedOut) setLoading(false); });
    return () => { clearTimeout(timer); controller.abort(); };
  }, [productId, attempt]);

  return <section className="product-detail-page" aria-busy={loading}>
    <a className="back-to-results" href="#">&#8592; Back to recommendations</a>
    {loading && <div className="loading" role="status"><span className="spinner"/><p>Loading product details...</p></div>}
    {error && <div className="notice error" role="alert"><p>{error}</p><button type="button" className="detail-retry" onClick={() => setAttempt(value => value + 1)}>Try again</button></div>}
    {product && <ProductDetailsContent key={product.product_id} product={product} />}
  </section>;
}
