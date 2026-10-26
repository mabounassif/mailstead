import assert from "node:assert/strict";
import test from "node:test";
import { messageChatCoversTabs } from "./navigation";

test("chat list keeps the tab bar", () => {
  assert.equal(messageChatCoversTabs("/messages"), false);
  assert.equal(messageChatCoversTabs("/messages/"), false);
  assert.equal(messageChatCoversTabs("/drive"), false);
});

test("an open conversation covers the tab bar", () => {
  assert.equal(messageChatCoversTabs("/messages/thread"), true);
  assert.equal(messageChatCoversTabs("/messages/thread?dm=ada"), true);
  assert.equal(messageChatCoversTabs("/messages/copy/12"), true);
  assert.equal(messageChatCoversTabs("/messages/new"), true);
});
