import { CalendarDays, Laptop, Gift, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
const steps = [
  ["01",CalendarDays,"Choose an Occasion","Tell us the occasion, like Birthday, Wedding, Anniversary or Diwali."],
  ["02",Laptop,"Get Personalized Suggestions","Our AI searches the product catalog and finds the most relevant gifts for your occasion."],
  ["03",Gift,"Select the Perfect Gift","Explore the recommended options and pick the one that suits your needs best."],
];
export default function HowItWorks() {
  return <main className="page inner-page works-page"><div className="works-background"><img src="/images/side-gifts.webp" alt=""/></div>
    <div className="content-wrap"><header className="center-heading"><span className="eyebrow">Simple, thoughtful, personal</span><h1>How It Works <span className="sparkle-accent">✳</span></h1><p>Find meaningful gifts in three simple steps.</p></header>
    <div className="steps-grid">{steps.map(([num,Icon,title,desc],i)=><div className="step-wrap" key={num}><article className="step-card"><span className="step-number">{num}</span><div className="step-illustration"><Icon size={112} strokeWidth={1.2}/></div><h2>{title}</h2><p>{desc}</p></article>{i<2 && <span className="step-arrow"><ArrowRight size={20}/></span>}</div>)}</div>
    <div className="works-cta"><Link to="/" className="btn btn-olive">Find your next gift <ArrowRight size={17}/></Link></div>
    </div></main>;
}