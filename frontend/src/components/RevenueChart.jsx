import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import { formatCurrency } from "../utils/format";

function RevenueChart({ data }) {
  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h3>Monthly Revenue Trend</h3>
          <p>Revenue performance over time</p>
        </div>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />

            <XAxis dataKey="Order_Date" tick={{ fontSize: 12 }} />

            <YAxis
              tickFormatter={(value) => `$${(value / 1000000).toFixed(0)}M`}
              tick={{ fontSize: 12 }}
            />

            <Tooltip
              formatter={(value) => [formatCurrency(value), "Revenue"]}
            />

            <Line
              type="monotone"
              dataKey="Revenue"
              stroke="#4f46e5"
              strokeWidth={3}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default RevenueChart;