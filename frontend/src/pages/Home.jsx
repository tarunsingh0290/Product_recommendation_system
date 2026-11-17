import { Zap, Layers, ShieldCheck } from "lucide-react";
import OccasionSearch from "../components/OccasionSearch.jsx";
const features = [
  [Zap,"Quick & Simple","Enter an occasion and get ideas instantly"],
  [Layers,"Curated Collection","Thoughtfully selected gifts"],
  [ShieldCheck,"Relevant Results","Suggestions that match your occasion"],
];
export default function Home() {
  return <main className="page home-page"><section className="home-hero content-wrap">
    <div className="home-copy"><span className="eyebrow">A little thought goes a long way</span>
      <h1>The Right Gift<br/>for Every <em>Occasion</em></h1>
      <p>Discover thoughtful and relevant gift suggestions from our curated collection.</p>
      <OccasionSearch/>
    </div>
    <div className="home-art" aria-label="Gift boxes with olive ribbons" role="img"><img src="/images/home-gifts.webp" alt=""/></div>
  </section>
  <section className="home-features content-wrap" aria-label="Why choose Giftly">
    {features.map(([Icon,title,subtitle]) => <div className="home-feature" key={title}><span className="feature-circle"><Icon size={23}/></span><div><h2>{title}</h2><p>{subtitle}</p></div></div>)}
  </section></main>;
}