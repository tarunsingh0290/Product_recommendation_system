import React, { useState } from 'react';

export default function ProductCard({ product, index }) {
  const [failed, setFailed] = useState(false);
  const price = product.price == null ? null : product.currency
    ? new Intl.NumberFormat(undefined, { style: 'currency', currency: product.currency }).format(product.price)
    : new Intl.NumberFormat().format(product.price);
  return <article className="product-card">
    <a className="product-card-link" href={`#product/${encodeURIComponent(product.product_id)}`} aria-label={`View details for ${product.name}`}>
      <div className="product-image">
        {product.image_url && !failed
          ? <img src={product.image_url} alt={product.name} loading="lazy" onError={() => setFailed(true)} />
          : <span className="image-fallback" aria-label="No product image">&#10023;</span>}
        <span className="product-number">{String(index + 1).padStart(2, '0')}</span>
      </div>
      <div className="product-copy">
        <p className="eyebrow">{product.brand || 'Brand not specified'}</p>
        <h3>{product.name}</h3>
        <p className="price"><span className="price-label">Price </span>{price === null ? 'Not listed' : price}</p>
        <p className="similarity-score">Cosine similarity: {product.similarity_score.toFixed(4)}</p>
        {product.suitability_passed === false && <p className="suitability-caution">Suitability caution: this product may not fit your occasion.</p>}
        {product.category && <span className="category">{product.category}</span>}
        <p className="reason"><span aria-hidden="true">&#10023; </span>{product.reason}</p>
        <span className="view-product">View product details <span aria-hidden="true">&#8599;</span></span>
      </div>
    </a>
  </article>;
}
