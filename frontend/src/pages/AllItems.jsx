import { useEffect, useMemo, useState } from "react";
import { Search, ChevronLeft, ChevronRight, Gift, Flower2, Coffee, Gem, Headphones } from "lucide-react";
import { getCatalog } from "../services/api.js";
import ProductCard from "../components/ProductCard.jsx";
import StatePanel from "../components/StatePanel.jsx";

const tags = [
  ["All Items", Gift], ["Gift Hampers", Gift], ["Flowers", Flower2],
  ["Chocolates", Gem], ["Personalized", Gift],
  ["Home & Living", Coffee], ["Gadgets", Headphones],
];
const PAGE_SIZE = 8;

export default function AllItems() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState("All Items");
  const [page, setPage] = useState(1);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    getCatalog({ signal: controller.signal })
      .then(items => { if (!controller.signal.aborted) setProducts(items); })
      .catch(err => { if (!controller.signal.aborted && err.name !== "AbortError") setError(err.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [retry]);

  const matched = useMemo(() => {
    const text = query.trim().toLowerCase();
    const categoryTerm = selected === "All Items" ? "" : selected.toLowerCase();
    return products.filter(product => {
      const combined = [product.name, product.brand, product.description, product.shortDescription,
        product.category, product.categoryName].filter(Boolean).join(" ").toLowerCase();
      return (!text || combined.includes(text)) && (!categoryTerm || combined.includes(categoryTerm));
    });
  }, [products, query, selected]);
  const totalPages = Math.max(1, Math.ceil(matched.length / PAGE_SIZE));
  const visible = matched.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return <main className="page inner-page catalog-page">
    <div className="catalog-decor"><img src="/images/side-gifts.webp" alt=""/></div>
    <div className="catalog-main content-wrap">
      <header className="catalog-heading"><div><span className="eyebrow">Explore the collection</span>
        <h1>All Items <span className="sparkle-accent">✳</span></h1>
        <p>Explore every product in our gift collection.</p></div>
        <label className="search-small"><Search size={19}/><input value={query} type="search"
          placeholder="Search gifts, categories, or brands..."
          onChange={e => { setQuery(e.target.value); setPage(1); }} aria-label="Search products" /></label>
      </header>
      <div className="catalog-tags" aria-label="Explore product categories">
        {tags.map(([tag, Icon]) => <button type="button" key={tag}
          className={selected === tag ? "filter-chip active" : "filter-chip"}
          onClick={() => { setSelected(tag); setPage(1); }} aria-pressed={selected === tag}>
          <Icon size={15}/>{tag}</button>)}
      </div>
      {loading ? <div className="product-grid">{Array.from({length: 8}, (_, i) =>
          <div className="product-card skeleton" key={i}><div className="product-media"/><div className="skeleton-lines"/></div>)}</div>
        : error ? <StatePanel variant="error" title="Unable to load products" message={error} onRetry={() => setRetry(v => v + 1)}/>
        : !visible.length ? <StatePanel title="No matching gifts" message="Try a different search or select All Items."/>
        : <div className="product-grid">{visible.map(p => <ProductCard key={p.product_id} product={p}/>)}</div>}
      {!loading && !error && matched.length > 0 && <div className="pagination">
        <p>Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, matched.length)} of {matched.length} items</p>
        <div className="page-controls">
          <button aria-label="Previous page" disabled={page <= 1} onClick={() => setPage(p => p - 1)}><ChevronLeft size={18}/></button>
          <span className="page-current">{page}</span><span>of {totalPages}</span>
          <button aria-label="Next page" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}><ChevronRight size={18}/></button>
        </div></div>}
    </div>
  </main>;
}
