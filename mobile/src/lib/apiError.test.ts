import assert from "node:assert/strict";
import test from "node:test";
import { ApiError, errorFromResponse, messageFromApiError } from "./apiError";

test("errorFromResponse prefers a field message", async () => {
  const response = new Response(
    JSON.stringify({
      error: "invalid",
      detail: "Could not send.",
      fields: { body: ["Write a message first."] },
    }),
    { status: 400, headers: { "Content-Type": "application/json" } },
  );
  const error = await errorFromResponse(response);
  assert.equal(error.code, "invalid");
  assert.equal(messageFromApiError(error), "Write a message first.");
});

test("messageFromApiError falls back to the detail", () => {
  const error = new ApiError(429, "locked", "Too many sign-in attempts. Try again later.");
  assert.equal(messageFromApiError(error), "Too many sign-in attempts. Try again later.");
});
