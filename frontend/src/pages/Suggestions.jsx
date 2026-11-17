import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Sparkles } from "lucide-react";
import OccasionSearch from "../components/OccasionSearch.jsx";
import ProductCard from "../components/ProductCard.jsx";
import StatePanel from "../components/StatePanel.jsx";
import { getRecommendations } from "../services/api.js";
export default function Suggestions() {
  const [params] = useSearchParams();
  const occasion = (params.get("occasion") || "").trim();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [retry,setRetry] = useState(0);
  useEffect(()=>{
    if (!occasion) {setResult(null);setError("");setLoading(false);return;}
    const controller = new AbortController();
    setLoading(true);setResult(null);setError("");
    getRecommendations(occasion, controller.signal).then(data=>{if(!controller.signal.aborted)setResult(data);}).catch(e=>{if(e.name!=="AbortError"&&!controller.signal.aborted)setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
    return ()=>controller.abort();
  },[occasion,retry]);
  const items = Array.isArray(result?.recommendations) ? result.recommendations : [];
  return <main className="page inner-page suggestions-page"><div className="suggestions-decor"><img src="/images/side-gifts.webp" alt=""/></div>
    <div className="content-wrap suggestions-content"><div className="suggestions-top"><div><h1>Gift <em>Suggestion</em><span className="sparkle-accent"> ✳</span></h1><p>Find thoughtful gifts for every occasion<br/>from our curated collection.</p></div>
      <OccasionSearch key={occasion} compact initial={occasion}/>
    </div>
    <div className="results-heading"><h2><Sparkles size={22}/>Recommended Gifts {occasion && <>for <em>{occasion}</em></>}</h2>{!loading && !error && items.length > 0 && <span className="results-count">✦ Top {items.length} suggestions</span>}</div>
    {!occasion ? <StatePanel title="Which occasion are we celebrating?" message="Enter an occasion above to discover matching gifts."/>
      : loading ? <div className="recommendation-grid">{Array.from({length:10},(_,i)=><div className="product-card skeleton" key={i}><div className="product-media"/><div className="skeleton-lines"/></div>)}</div>
      : error ? <StatePanel variant="error" title="Could not generate suggestions" message={error} onRetry={()=>setRetry(n=>n+1)}/>
      : !items.length ? <StatePanel title="No gifts matched this time" message="Try a different occasion or search again." onRetry={()=>setRetry(n=>n+1)}/>
      : <div className="recommendation-grid">{items.map((p,i)=><ProductCard key={p.product_id || i} product={p} rank={i+1}/>)}</div>}
    </div>
  </main>;
}