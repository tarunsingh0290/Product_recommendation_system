import { Target, Layers, Zap, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
const values = [[Target,"Occasion Focused","Get gifts tailored to your celebrations"],[Layers,"Smart & Relevant","AI-powered matching from our product catalog"],[Zap,"Quick & Simple","Enter an occasion and get instant recommendations"]];
export default function About() {
  return <main className="page about-page"><div className="content-wrap about-grid"><section className="about-copy"><span className="pill-label">About Giftly</span><h1>The smarter way<br/>to find the <em>perfect gift</em></h1><p>Giftly is an occasion-based gift recommendation system that helps you discover thoughtful and relevant gifts from a curated product catalog.</p>
    <div className="about-values">{values.map(([Icon,title,desc])=><div className="value-item" key={title}><span className="value-icon"><Icon size={28}/></span><h2>{title}</h2><p>{desc}</p></div>)}</div>
    <Link to="/" className="btn btn-olive about-cta">Find a gift <ArrowRight size={17}/></Link>
  </section><aside className="about-art"><img src="/images/about-gifts.webp" alt="Gift boxes wrapped with green ribbon"/></aside></div></main>;
}