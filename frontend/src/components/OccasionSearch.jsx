import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, ArrowRight, Cake, Heart, CalendarHeart, Sparkles, Gift } from "lucide-react";
const occasions = [
  ["Birthday",Cake], ["Wedding",Heart], ["Anniversary",CalendarHeart], ["Diwali",Sparkles], ["Thank You",Gift]
];
export default function OccasionSearch({ initial = "", compact = false, showChips = true }) {
  const [value, setValue] = useState(initial);
  const navigate = useNavigate();
  const submit = text => { const occasion=text.trim(); if(occasion) navigate(`/suggestions?occasion=${encodeURIComponent(occasion)}`); };
  return <div className={compact ? "occasion-widget compact" : "occasion-widget"}>
    <form className="occasion-input" onSubmit={e => { e.preventDefault(); submit(value); }}>
      <Search size={20} aria-hidden="true" />
      <input type="text" value={value} onChange={e => setValue(e.target.value)} maxLength={100} placeholder="Enter an occasion (e.g., Birthday, Wedding, Diwali)" aria-label="Occasion" required />
      <button type="submit" className="btn btn-olive">Find Gifts <ArrowRight size={17}/></button>
    </form>
    {showChips && <div className="popular-chips"><strong>Popular Occasions:</strong><div className="chips">
      {occasions.map(([name,Icon]) => <button type="button" key={name} className="chip" onClick={() => submit(name)}><Icon size={15}/>{name}</button>)}
    </div></div>}
  </div>;
}