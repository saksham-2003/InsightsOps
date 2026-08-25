import { DollarSign, TrendingUp, ShoppingCart, Percent } from "lucide-react";

import KpiCard from "./kpiCard";
import { formatCurrency, formatNumber } from "../utils/format";

function KPISection({ kpis }) {
  return (
    <section className="kpi-grid">
      <KpiCard
        title="Total Revenue"
        value={formatCurrency(kpis.total_revenue)}
        subtitle="Across all transactions"
        icon={<DollarSign size={22} />}
      />

      <KpiCard
        title="Total Profit"
        value={formatCurrency(kpis.total_profit)}
        subtitle="Net business profit"
        icon={<TrendingUp size={22} />}
      />

      <KpiCard
        title="Total Orders"
        value={formatNumber(kpis.total_orders)}
        subtitle="Completed transactions"
        icon={<ShoppingCart size={22} />}
      />

      <KpiCard
        title="Profit Margin"
        value={`${kpis.profit_margin.toFixed(2)}%`}
        subtitle="Overall profitability"
        icon={<Percent size={22} />}
      />
    </section>
  );
}

export default KPISection;
