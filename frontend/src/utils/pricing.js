const number = value => {
  if (value === undefined || value === null || value === "") return null;
  const n = Number(String(value).replace(/[₹,\s]/g, ""));
  return Number.isFinite(n) && n >= 0 ? n : null;
};
export const money = value => {
  const amount = number(value);
  return amount === null ? "Price unavailable" : `₹${amount.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;
};
export function pricing(product = {}) {
  const original = number(product.price);
  const percentage = number(product.discountPercentage);
  const explicitDiscounted = number(product.discountedPrice);
  const explicitAmount = number(product.discountAmount);
  // Catalog price represents original price; calculate the discounted amount.
  const percentValid = percentage !== null && percentage > 0 && percentage <= 100;
  const discounted = explicitDiscounted !== null ? explicitDiscounted
    : original !== null && percentValid ? Math.round(original * (100 - percentage)) / 100
    : original !== null && explicitAmount !== null ? Math.max(0, original - explicitAmount)
    : original;
  const savings = original !== null && discounted !== null ? Math.max(0, original - discounted) : null;
  const effectivePercent = percentValid ? percentage
    : savings !== null && original > 0 ? Math.round((savings / original) * 100) : 0;
  return {
    original, discounted, savings,
    percentage: effectivePercent,
    onSale: original !== null && savings !== null && savings > 0,
  };
}
