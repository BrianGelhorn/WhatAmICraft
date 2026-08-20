import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const eslintVersion = require("eslint/package.json").version;

assert.equal(eslintVersion, "9.19.0");
const { default: config } = await import("../eslint.config.mjs");
assert.ok(Array.isArray(config) && config.length > 0);

console.log(`lint toolchain: ESLint ${eslintVersion}, Remotion config loaded`);
