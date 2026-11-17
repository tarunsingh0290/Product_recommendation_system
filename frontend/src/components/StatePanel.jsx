import { AlertCircle, RefreshCw, Gift } from "lucide-react";
export default function StatePanel({ variant = "empty", title, message, onRetry }) {
  const Icon = variant === "error" ? AlertCircle : Gift;
  return <div className={`state-panel ${variant}`} role={variant === "error" ? "alert" : "status"}>
    <Icon size={37}/><h3>{title}</h3><p>{message}</p>
    {onRetry && <button className="btn btn-olive" onClick={onRetry}><RefreshCw size={16}/>Try again</button>}
  </div>;
}