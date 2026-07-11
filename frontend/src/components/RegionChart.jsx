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

function RegionChart({ data }) {
  return (
    <div className="chart-card half-chart">
      <div className="chart-header">
        <div>
          <h3>Regional Performance</h3>
          <p>Revenue comparison across regions</p>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />

            <XAxis
              type="number"
              tickFormatter={(value) => `$${(value / 1000000).toFixed(0)}M`}
              tick={{ fontSize: 11 }}
            />

            <YAxis
              type="category"
              dataKey="Region"
              tick={{ fontSize: 12 }}
              width={60}
            />

            <Tooltip
              formatter={(value) => [formatCurrency(value), "Revenue"]}
            />

            <Bar dataKey="Revenue" fill="#6366f1" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default RegionChart;