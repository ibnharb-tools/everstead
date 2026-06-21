export const fmtMoney = (n, currency = 'CAD') => {
  if (n == null) return 'Not applicable';
  return new Intl.NumberFormat('en', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(n);
};

export const fmtNum = (n) => {
  if (n == null) return '-';
  return new Intl.NumberFormat('en').format(Math.round(n));
};

export const fmtPayback = (n) => {
  if (n == null) return 'Not a payback fit';
  return `${n} years`;
};

export const fmtDate = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
};
