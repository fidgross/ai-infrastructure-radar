function normalizeApiBaseUrl(value: string): string {
  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value.replace(/\/+$/, "");
  }
  return `http://${value}`.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  const configured = process.env.INTERNAL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  return normalizeApiBaseUrl(configured);
}
