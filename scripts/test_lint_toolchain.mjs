import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const eslintVersion = require("eslint/package.json").version;
const reactVersion = require("react/package.json").version;
const reactDomVersion = require("react-dom/package.json").version;
const remotionPackages = [
  "remotion",
  "@remotion/captions",
  "@remotion/cli",
  "@remotion/media",
  "@remotion/eslint-config-flat",
].map((name) => require(`${name}/package.json`).version);

assert.equal(eslintVersion, "9.19.0");
assert.equal(reactVersion, reactDomVersion);
assert.equal(new Set(remotionPackages).size, 1);
const lock = JSON.parse(readFileSync(new URL("../package-lock.json", import.meta.url)));
const remotionLock = lock.packages["node_modules/remotion"];
const compositorPackages = Object.keys(remotionLock.optionalDependencies ?? {});
assert.ok(compositorPackages.length > 0);
for (const name of compositorPackages) {
  assert.equal(lock.packages[`node_modules/${name}`]?.version, remotionPackages[0]);
}
const { default: config } = await import("../eslint.config.mjs");
assert.ok(Array.isArray(config) && config.length > 0);

console.log(
  `toolchain: ESLint ${eslintVersion}, React ${reactVersion}, Remotion ${remotionPackages[0]}`,
);
