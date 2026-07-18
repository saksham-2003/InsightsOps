export const formatCurrency = (value) => {
  // Handle null/undefined
  if (value === null || value === undefined) {
    return "$0.00";
  }

  // Handle arrays (used by confidence bands)
  if (Array.isArray(value)) {
    return `${formatCurrency(value[0])} - ${formatCurrency(value[1])}`;
  }

  // Convert strings to numbers if possible
  const num = Number(value);

  // Handle invalid values
  if (Number.isNaN(num)) {
    return "$0.00";
  }

  if (num >= 1000000) {
    return `$${(num / 1000000).toFixed(1)}M`;
  }

  if (num >= 1000) {
    return `$${(num / 1000).toFixed(1)}K`;
  }

  return `$${num.toFixed(2)}`;
};

export const formatNumber = (value) => {
  if (value === null || value === undefined) return "0";

  const num = Number(value);

  if (Number.isNaN(num)) return "0";

  return new Intl.NumberFormat("en-US").format(num);
};

