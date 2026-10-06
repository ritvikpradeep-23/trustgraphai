import { test } from "node:test";
import assert from "node:assert/strict";
import { validatePasswordChange } from "../src/lib/passwordValidation.ts";

test("password change requires current password, strong new passphrase and matching confirmation", () => {
  assert.ok(validatePasswordChange("", "a long new passphrase", "a long new passphrase"));
  assert.ok(validatePasswordChange("old", "short", "short"));
  assert.ok(validatePasswordChange("old", " ".repeat(20), " ".repeat(20)));
  assert.ok(validatePasswordChange("old", "x".repeat(129), "x".repeat(129)));
  assert.ok(validatePasswordChange("a long old passphrase", "a long old passphrase", "a long old passphrase"));
  assert.ok(validatePasswordChange("old", "a long new passphrase", "different confirmation"));
  assert.equal(validatePasswordChange("old", "a long new passphrase", "a long new passphrase"), null);
});
