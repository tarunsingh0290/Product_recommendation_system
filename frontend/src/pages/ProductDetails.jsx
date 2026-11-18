import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ArrowLeft, Gift, Tag, BadgePercent } from "lucide-react";
import { getProduct, normalizeProduct } from "../services/api.js";
import { pricing, money } from "../utils/pricing.js";
import StatePanel from "../components/StatePanel.jsx";

export default function ProductDetails() {
  const { productId } = useParams();
  const location = useLocation();
  const preview = location.state?.product ? normalizeProduct(location.state.product) : null;
  const [product, setProduct] = useState(preview);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [imageFailed, setImageFailed] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(""); setImageFailed(false);
    getProduct(productId, { signal: controller.signal })
      .then(full => { if (!controller.signal.aborted) setProduct(prev => {
        const merged = { ...prev, ...full };
        for (const key of ["brand", "originalPrice", "discountedPrice", "discountPercentage", "discountAmount", "description", "shortDescription", "mainImage"]) {
          if (merged[key] == null || merged[key] === "") merged[key] = prev?.[key];
        }
        return merged;
      }); })
      .catch(err => { if (!controller.signal.aborted && err.name !== "AbortError") setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [productId, retry]);

  const discount = pricing(product || {});
  return (
    <main className="page product-details-page content-wrap">
      <Link className="back-link" to="/all-items"><ArrowLeft size={18} /> Back to All Items</Link>
      {!product && loading ? <StatePanel title="Loading product details" message="Getting full product information..." />
        : !product && error ? <StatePanel variant="error" title="Could not load product" message={error} onRetry={() => setRetry(n => n + 1)} />
        : product ? <>
          {error && <p className="details-warning">Some details could not be refreshed: {error}</p>}
          <div className="details-grid">
            <div className="details-visual">
              {product.mainImage && !imageFailed ? <img src={product.mainImage} alt={product.name} onError={() => setImageFailed(true)}/>
                : <div className="image-fallback"><Gift size={90}/><span>Giftly</span></div>}
              {discount.onSale && <span className="details-sale-badge"><BadgePercent size={18}/>{discount.percentage}% OFF</span>}
            </div>
            <section className="details-information">
              <span className="eyebrow">Giftly collection</span>
              <div className="details-brand"><Tag size={16}/>{product.brand || "Brand not specified"}</div>
              <h1>{product.name}</h1>
              {product.shortDescription && <p className="details-short">{product.shortDescription}</p>}
              <div className="details-price-row">
                <strong>{money(discount.discounted)}</strong>
                {discount.onSale && <><del>{money(discount.original)}</del><span className="details-percent">{discount.percentage}% OFF</span></>}
              </div>
              {discount.onSale && <p className="details-save">You save {money(discount.savings)} on this gift.</p>}
              <div className="details-specs">
                <div><span>Brand</span><strong>{product.brand || "Not specified"}</strong></div>
                <div><span>Original price</span><strong>{money(discount.original)}</strong></div>
                <div><span>Discount</span><strong>{discount.onSale ? money(discount.savings) : "No discount"}</strong></div>
                <div><span>Discount percentage</span><strong>{discount.onSale ? `${discount.percentage}%` : "0%"}</strong></div>
                <div><span>Discounted price</span><strong>{money(discount.discounted)}</strong></div>
              </div>
              <div className="details-description"><h2>Description</h2><p>{product.description || "Detailed description is not available from the product API."}</p></div>
              <div className="details-description"><h2>Short description</h2><p>{product.shortDescription || "Short description is not available from the product API."}</p></div>
            </section>
          </div>
        </> : <StatePanel title="Product unavailable" message="This product could not be found." />}
    </main>
  );
}
