import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Gift, Menu, X, ExternalLink } from "lucide-react";
const routes = [
  ["/", "Home"], ["/all-items", "All Items"],
  ["/how-it-works", "How It Works"], ["/about", "About"],
];
export default function Navbar() {
  const [expanded, setExpanded] = useState(false);
  return <header className="site-header"><div className="nav-inner">
    <Link className="brand" to="/" onClick={() => setExpanded(false)}><span className="brand-icon"><Gift size={28}/></span><span>Giftly</span></Link>
    <span className="brand-tagline">Occasion-Based Gift Recommendation</span>
    <button className="mobile-menu-toggle" type="button" aria-label={expanded ? "Close menu" : "Open menu"} aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? <X/> : <Menu/>}</button>
    <nav className={expanded ? "nav-links open" : "nav-links"} aria-label="Main navigation">
      {routes.map(([path,label]) => <NavLink key={path} to={path} end={path === "/"} onClick={() => setExpanded(false)} className={({isActive}) => `nav-link${isActive ? " active" : ""}`}>{label}</NavLink>)}
      <a className="nav-external" href="https://github.com/tarunsingh0290/Product_recommendation_system" target="_blank" rel="noopener noreferrer" aria-label="View project on GitHub" title="View project on GitHub"><ExternalLink size={20}/></a>
    </nav>
  </div></header>;
}