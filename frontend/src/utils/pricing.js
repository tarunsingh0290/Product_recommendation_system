function number(value) {
  if (value === undefined || value === null || value === "") return null;
  const n = Number(String(value).replace(/[₹,%\s,]/g, ""));
  return Number.isFinite(n) && n >= 0 ? n : null;
}
export function money(value) {
  const amount = number(value);
  return amount === null ? "Price unavailable" : `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
}
export function pricing(product = {}) {
  // The supplied products.json uses price as original price and discountPercentage as percent off.
  const original = number(product.originalPrice ?? product.mrp ?? product.price);
  const suppliedPercent = number(product.discountPercentage ?? product.discount_percentage);
  const explicit = number(product.discountedPrice ?? product.discountPrice);
  const amount = number(product.discountAmount);
  let discounted = original;
  if (original !== null && explicit !== null && explicit <= original) discounted = explicit;
  else if (original !== null && suppliedPercent !== null && suppliedPercent <= 100)
    discounted = Math.round(original * (100 - suppliedPercent)) / 100;
  else if (original !== null && amount !== null)
    discounted = Math.max(0, original - amount);
  const savings = original !== null && discounted !== null ? Math.max(0, original - discounted) : 0;
  const percentage = original > 0 && savings > 0 ? Math.round(savings / original * 10000) / 100 : 0;
  return { original, discounted, savings, percentage, onSale: savings > 0 };
}
export const getPricing = pricing;
export const formatPrice = money;
