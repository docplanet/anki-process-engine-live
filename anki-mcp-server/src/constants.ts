const envUrl = process.env.ANKI_CONNECT_URL?.trim();
export const ANKI_CONNECT_URL = envUrl || "http://127.0.0.1:8765";
export const ANKI_CONNECT_API_KEY = process.env.ANKI_CONNECT_API_KEY;
export const ANKI_CONNECT_VERSION = 6;
export const CHARACTER_LIMIT = 25000;

const envTimeout = Number(process.env.ANKI_CONNECT_TIMEOUT_MS);
export const REQUEST_TIMEOUT_MS =
  Number.isFinite(envTimeout) && envTimeout > 0 ? envTimeout : 30_000;
// sync blocks until the full AnkiWeb sync finishes, which can take minutes
export const SYNC_TIMEOUT_MS = 300_000;
