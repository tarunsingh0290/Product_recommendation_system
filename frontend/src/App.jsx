import { Route, Routes, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import Navbar from "./components/Navbar.jsx";
import Home from "./pages/Home.jsx";
import AllItems from "./pages/AllItems.jsx";
import Suggestions from "./pages/Suggestions.jsx";
import HowItWorks from "./pages/HowItWorks.jsx";
import About from "./pages/About.jsx";
import ProductDetails from "./pages/ProductDetails.jsx";
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}
export default function App() {
  return <div className="app-shell"><ScrollToTop /><Navbar />
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/all-items" element={<AllItems />} />
      <Route path="/product/:productId" element={<ProductDetails />} />
      <Route path="/suggestions" element={<Suggestions />} />
      <Route path="/how-it-works" element={<HowItWorks />} />
      <Route path="/about" element={<About />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  </div>;
}