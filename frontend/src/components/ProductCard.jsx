import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Gift, ArrowUpRight } from "lucide-react";
import { pricing, money } from "../utils/pricing.js";

export default function ProductCard({ product, rank }) {
  const [broken, setBroken] = useState(false);
  useEffect(() => { setBroken(false); }, [product.mainImage]);
  const discount = pricing(product);
  const shortText = product.shortDescription || product.description || "Discover more about this gift.";
  return (
    <article className="product-card">
      <Link className="product-card-link" to={`/product/${encodeURIComponent(product.product_id)}`} state={{ product }} aria-label={`View details for ${product.name}`}>
        <div className="product-media">
          {product.mainImage && !broken
            ? <img src={product.mainImage} alt={product.name} loading="lazy" onError={() => setBroken(true)} />
            : <div className="image-fallback"><Gift size={48} /><span>Giftly</span></div>}
          {rank != null && <span className="rank-pill">{String(rank).padStart(2, "0")}</span>}
          {discount.onSale && <span className="discount-pill">{discount.percentage}% OFF</span>}
        </div>
        <div className="product-info">
          <span className="product-brand">{product.brand || "Brand not specified"}</span>
          <h3 title={product.name}>{product.name}</h3>
          <p title={shortText}>{shortText}</p>
          <div className="price-stack">
            <strong className="discounted-price">{money(discount.discounted)}</strong>
            {discount.onSale && <span className="original-price">{money(discount.original)}</span>}
          </div>
          {discount.onSale && <span className="savings-note">Save {money(discount.savings)} · {discount.percentage}% discount</span>}
          <span className="view-details">View details <ArrowUpRight size={15}/></span>
        </div>
      </Link>
    </article>
  );
}
