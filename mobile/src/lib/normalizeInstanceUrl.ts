export type NormalizedUrl = {
  /** Origin with no trailing slash, e.g. https://mail.example.com */
  origin: string;
};

export type NormalizeOptions = {
  /** When true, allow http:// (local development only). */
  allowInsecureHttp?: boolean;
};

/**
 * Normalize and validate a Mailstead instance URL.
 * Rejects non-http(s) schemes and empty hosts.
 */
export function normalizeInstanceUrl(
  raw: string,
  options: NormalizeOptions = {},
): NormalizedUrl | null {
  const trimmed = raw.trim();
  if (!trimmed) {
    return null;
  }

  let candidate = trimmed;
  if (!/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(candidate)) {
    candidate = `https://${candidate}`;
  }

  let url: URL;
  try {
    url = new URL(candidate);
  } catch {
    return null;
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") {
    return null;
  }
  if (!url.hostname) {
    return null;
  }

  if (url.protocol === "http:" && !options.allowInsecureHttp) {
    return null;
  }

  return { origin: url.origin };
}

export function sameOrigin(pageUrl: string, instanceOrigin: string): boolean {
  try {
    return new URL(pageUrl).origin === new URL(instanceOrigin).origin;
  } catch {
    return false;
  }
}
