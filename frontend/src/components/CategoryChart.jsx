import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { formatCurrency } from "../utils/format";

function CategoryChart({ data }) {
  return (
    <div className="chart-card half-chart">
      <div className="chart-header">
        <div>
          <h3>Category Performance</h3>
          <p>Revenue by product category</p>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />

            <XAxis dataKey="Category" tick={{ fontSize: 11 }} />

            <YAxis
              tickFormatter={(value) => `$${(value / 1000000).toFixed(0)}M`}
              tick={{ fontSize: 11 }}
            />

            <Tooltip
              formatter={(value) => [formatCurrency(value), "Revenue"]}
            />

            <Bar dataKey="Revenue" fill="#4f46e5" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default CategoryChart;