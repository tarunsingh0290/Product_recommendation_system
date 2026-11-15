import React, { useEffect, useState } from 'react';
import ProductCard from './components/ProductCard';
import GiftBackground from './components/GiftBackground';
import ProductDetails from './components/ProductDetails';
import { getRecommendations } from './services/api';

const occasions = ['Birthday', 'Wedding', 'Anniversary', 'Baby shower', 'Diwali', 'Housewarming', "Valentine's Day", 'Graduation', "Mother's Day", "Father's Day"];

function selectedProductId() {
  if (typeof window === 'undefined' || !window.location.hash.startsWith('#product/')) return null;
  try { return decodeURIComponent(window.location.hash.slice('#product/'.length)) || null; }
  catch { return null; }
}

export default function App() {
  const [occasion, setOccasion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [productId, setProductId] = useState(selectedProductId);

  useEffect(() => {
    const navigate = () => { setProductId(selectedProductId()); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', navigate);
    return () => window.removeEventListener('hashchange', navigate);
  }, []);

  async function submit(event) {
    event.preventDefault();
    if (loading) return;
    const value = occasion.trim();
    if (value.length < 2 || value.length > 100) {
      setError('Describe your occasion in 2–100 characters.'); return;
    }
    setLoading(true); setError(''); setResult(null);
    try { setResult(await getRecommendations(value, 10)); }
    catch (error) { setError(error.message); }
    finally { setLoading(false); }
  }

  return <>
    <GiftBackground />
    <header className="site-header"><a className="wordmark" href="/" aria-label="Product Recommendation System home"><span className="logo-mark" aria-hidden="true">&#10023;</span><span>Product Recommendation System<span className="dot">.</span></span></a><span className="header-note"><span className="status-dot"/> A little thought. A perfect gift.</span></header>
    <main>
      {productId ? <ProductDetails key={productId} productId={productId} /> : <>
      <section className="hero">
        <div className="hero-copy"><p className="eyebrow"><span className="tiny-line"/> EVERY OCCASION DESERVES SOMETHING SPECIAL</p>
          <h1>Great gifts.<br/>Better <em>recommendations.</em></h1>
          <p className="intro">Turn a special occasion into an unforgettable moment. Discover thoughtful gifts, matched to the celebration you have in mind.</p>
          <div className="hero-caption"><span>✧</span> Top 10 catalog matches, ranked by similarity.</div>
        </div>
        <div className="scene-caption" aria-hidden="true"><span className="scene-pill">A world of possibilities</span><span className="scene-coordinate">THOUGHTFULLY SELECTED &#183; JUST FOR YOU</span></div>
      </section>
      <section className="finder" aria-labelledby="finder-title">
        <div className="finder-heading"><span className="section-number">01 / THE OCCASION</span><h2 id="finder-title">What are we celebrating?</h2><p>Tell us the moment. We’ll help with the gift.</p></div>
        <form onSubmit={submit}>
          <div className="form-row"><div className="occasion-field"><label htmlFor="occasion">Your occasion</label><input id="occasion" value={occasion} onChange={e => setOccasion(e.target.value)} placeholder="e.g. An anniversary for my parents" minLength={2} maxLength={100} required disabled={loading}/></div>
            <div className="count-field"><span className="field-label">Recommendations</span><div className="fixed-count">10 top matches</div></div>
            <button className="submit" disabled={loading} type="submit">{loading ? 'Finding your gifts…' : 'Find thoughtful gifts'}<span aria-hidden="true">↗</span></button></div>
          <div className="occasion-chips"><span>A little inspiration</span>{occasions.map(item => <button key={item} type="button" aria-pressed={occasion === item} onClick={() => setOccasion(item)} disabled={loading}>{item}</button>)}</div>
        </form>
      </section>
      <div aria-live="polite" aria-busy={loading}>
        {error && <div className="notice error" role="alert"><strong>We couldn’t finish that search.</strong><p>{error}</p></div>}
        {loading && <section className="loading"><span className="spinner"/><h2>Finding a little something special</h2><p>Matching your occasion with gifts from our catalog. Busy periods can take a little longer; your search will retry automatically.</p></section>}
        {result && <section className="results"><div className="results-heading"><div><p className="eyebrow">02 / THE SHORTLIST</p><h2>Picked for {result.occasion.toLowerCase()}<span className="dot">.</span></h2></div><span>{result.returned_count} {result.returned_count === 1 ? 'catalog match' : 'catalog matches'}</span></div>
          {result.warning && <div className="notice" role="status">{result.warning}{result.retry_after_seconds && ` You can try for more in ${result.retry_after_seconds} seconds.`}</div>}
          {result.returned_count === 0 ? <div className="notice"><h3>No suitable gifts this time.</h3><p>Try a different occasion or add a little more detail.</p></div> : <><div className="product-grid">{result.recommendations.map((product, i) => <ProductCard key={product.product_id} product={product} index={i}/>)}</div>{result.returned_count < result.requested_count && <p className="fewer-note">We found {result.returned_count} catalog matches for your request of {result.requested_count}.</p>}</>}
        </section>}
        {!result && !loading && !error && <section className="how-it-works"><div><span>01</span><h3>Share the occasion</h3><p>A celebration, a milestone, a moment.</p></div><div><span>02</span><h3>Find a thoughtful match</h3><p>Selected for relevance from our catalog.</p></div><div><span>03</span><h3>Make someone’s day</h3><p>A shortlist to make choosing easier.</p></div></section>}
      </div>
      </>}
    </main>
    <footer><a className="footer-brand" href="/">Product Recommendation System<span className="dot">.</span></a><p>A little thought goes a long way.</p><span>FIND SOMETHING THAT MEANS SOMETHING</span></footer>
  </>;
}
