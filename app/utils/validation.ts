const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Returns true if the value is a valid UUID v4 string.
 * Use this to validate all IDs received from route params or external sources.
 */
export function isValidUUID(value: string): boolean {
    return UUID_RE.test(value);
}

/**
 * Strip control characters and unicode direction overrides that can spoof UI.
 */
export function sanitizeDisplay(s: string): string {
    return s.replace(/[\u0000-\u001F\u200B-\u200F\u202A-\u202E\uFEFF]/g, '').slice(0, 500);
}
