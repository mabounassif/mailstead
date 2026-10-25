import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { normalizeInstanceUrl, sameOrigin } from "./normalizeInstanceUrl";

describe("normalizeInstanceUrl", () => {
  it("adds https when scheme is missing", () => {
    assert.deepEqual(normalizeInstanceUrl("mail.example.com"), {
      origin: "https://mail.example.com",
    });
  });

  it("strips path and query from the stored origin", () => {
    assert.deepEqual(
      normalizeInstanceUrl("https://mail.example.com/inbox?x=1"),
      { origin: "https://mail.example.com" },
    );
  });

  it("rejects non-http schemes", () => {
    assert.equal(normalizeInstanceUrl("ftp://mail.example.com"), null);
  });

  it("rejects http unless allowInsecureHttp is set", () => {
    assert.equal(normalizeInstanceUrl("http://mail.example.com"), null);
    assert.deepEqual(
      normalizeInstanceUrl("http://10.0.0.2:8000", {
        allowInsecureHttp: true,
      }),
      { origin: "http://10.0.0.2:8000" },
    );
  });
});

describe("sameOrigin", () => {
  it("compares origins only", () => {
    assert.equal(
      sameOrigin("https://mail.example.com/a", "https://mail.example.com"),
      true,
    );
    assert.equal(
      sameOrigin("https://evil.example/a", "https://mail.example.com"),
      false,
    );
  });
});
