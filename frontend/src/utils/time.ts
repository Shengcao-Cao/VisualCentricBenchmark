export function toRelativeLabel(value: number | string | Date): string {
  const ts = typeof value === "number" ? value : new Date(value).getTime();
  const diffMs = Date.now() - ts;
  const oneDay = 24 * 60 * 60 * 1000;

  if (diffMs < oneDay) {
    return "today";
  }
  if (diffMs < oneDay * 2) {
    return "yesterday";
  }
  return `${Math.max(2, Math.floor(diffMs / oneDay))} days ago`;
}

