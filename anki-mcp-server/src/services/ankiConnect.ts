import { z } from "zod";
import {
  ANKI_CONNECT_API_KEY,
  ANKI_CONNECT_URL,
  ANKI_CONNECT_VERSION,
  REQUEST_TIMEOUT_MS,
} from "../constants.js";
import type { AnkiConnectResponse } from "../types.js";

export class AnkiConnectError extends Error {}

export async function invoke<T>(
  action: string,
  params?: object,
  options?: { timeoutMs?: number }
): Promise<T> {
  const timeoutMs = options?.timeoutMs ?? REQUEST_TIMEOUT_MS;
  let response: Response;
  try {
    response = await fetch(ANKI_CONNECT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        version: ANKI_CONNECT_VERSION,
        params,
        ...(ANKI_CONNECT_API_KEY ? { key: ANKI_CONNECT_API_KEY } : {}),
      }),
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof Error && error.name === "TimeoutError") {
      throw new AnkiConnectError(
        `AnkiConnect did not respond within ${timeoutMs / 1000}s (action "${action}"). ` +
          `Anki may be blocked by a modal dialog or a long-running operation — check the Anki window.`
      );
    }
    const cause = error instanceof Error ? error.message : String(error);
    throw new AnkiConnectError(
      `Could not reach AnkiConnect at ${ANKI_CONNECT_URL} (${cause}). Make sure Anki is running and the ` +
        `AnkiConnect add-on is installed (Tools → Add-ons → Get Add-ons… → code 2055492159 → restart Anki).`
    );
  }

  if (!response.ok) {
    throw new AnkiConnectError(`AnkiConnect request failed with HTTP status ${response.status}`);
  }

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new AnkiConnectError(
      `The server at ${ANKI_CONNECT_URL} returned a non-JSON response — it may not be AnkiConnect. ` +
        `Make sure Anki (with the AnkiConnect add-on) is what's listening on this port.`
    );
  }

  if (typeof body !== "object" || body === null || !("result" in body) || !("error" in body)) {
    throw new AnkiConnectError(
      `The server at ${ANKI_CONNECT_URL} did not return an AnkiConnect response envelope — it may not be AnkiConnect.`
    );
  }

  const { result, error } = body as AnkiConnectResponse<T>;
  if (error) {
    throw new AnkiConnectError(`AnkiConnect error: ${error}`);
  }
  return result;
}

export function handleAnkiError(error: unknown): string {
  if (error instanceof AnkiConnectError) {
    return `Error: ${error.message}`;
  }
  if (error instanceof z.ZodError) {
    const issues = error.issues
      .map((issue) => `${issue.path.join(".") || "(input)"}: ${issue.message}`)
      .join("; ");
    return `Error: Invalid input — ${issues}`;
  }
  return `Error: Unexpected error occurred: ${error instanceof Error ? error.message : String(error)}`;
}
