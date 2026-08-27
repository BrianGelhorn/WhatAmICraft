#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
    args[key] = value;
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
if (!args.version || !args.name) {
  console.error("Usage: node extract_minecraft_data.mjs --version <version> --name <canonical_name> [--out file.json]");
  process.exit(2);
}

let minecraftData;
try {
  const projectRequire = createRequire(path.join(process.cwd(), "package.json"));
  minecraftData = projectRequire("minecraft-data");
} catch (error) {
  console.error("minecraft-data is not installed in the current project. Run: npm install minecraft-data");
  process.exit(3);
}

const mc = minecraftData(String(args.version));
const block = mc.blocksByName?.[args.name];
const item = mc.itemsByName?.[args.name];
if (!block && !item) {
  console.error(`Unknown block/item '${args.name}' for Minecraft ${args.version}`);
  process.exit(4);
}

const entity = block ?? item;
const food = Boolean(mc.foodsByName?.[args.name]);
const weaponNames = /(?:sword|bow|crossbow|trident|mace)$/.test(args.name);
const toolNames = /(?:pickaxe|shovel|hoe|fishing_rod|shears|flint_and_steel|brush)$/.test(args.name);
const kind = block ? "block" : food ? "food" : weaponNames ? "weapon" : toolNames ? "tool" : "item";
const itemRecord = item ?? (block?.drops?.length === 1 ? mc.items?.[block.drops[0]] : undefined);
const recipes = itemRecord ? (mc.recipes?.[itemRecord.id] ?? []) : [];
const resolveItem = (id) => mc.items?.[id]?.name ?? `item_id:${id}`;

const facts = [];
const add = (id, type, value, scope = "target", verified = true, note) => {
  if (value !== undefined && value !== null) {
    facts.push({ id, type, relation: type, semantic_key: id, value, scope, source_type: "minecraft-data", source: `minecraft-data ${args.version}`, verified, ...(note ? { note } : {}) });
  }
};

add("structured_kind", "kind", kind, "family");
add("structured_stack", "stack_size", entity.stackSize, "family");
if (block) {
  add("structured_material", "material", block.material, "family");
  add("structured_hardness", "hardness", block.hardness);
  add("structured_resistance", "resistance", block.resistance);
  add("structured_diggable", "diggable", block.diggable);
  add("structured_transparent", "transparent", block.transparent);
  add("structured_light", "emitted_light", block.emitLight);
  add("structured_bounding_box", "bounding_box", block.boundingBox, "family");
  add("structured_drops", "drops", (block.drops ?? []).map(resolveItem));
  add("structured_tools", "harvest_tools", Object.keys(block.harvestTools ?? {}).map((id) => resolveItem(Number(id))));
}
if (recipes.length) {
  add("structured_recipes", "recipes", recipes.map((recipe) => ({
    ingredients: (recipe.ingredients ?? recipe.inShape?.flat() ?? []).filter((v) => v !== null).map((v) => ({
      raw: v,
      resolved_name: resolveItem(typeof v === "number" ? v : v.id)
    })),
    result_count: recipe.result?.count ?? 1
  })), "variant", false, "Recipe entries can encode tags or alternatives; confirm the applicable ingredients in Minecraft Wiki before turning this into a clue.");
}

const colorNames = new Set(["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray", "cyan", "purple", "blue", "brown", "green", "red", "black"]);
const parts = args.name.split("_");
let variant;
let family = args.name;
for (const color of [...colorNames].sort((a, b) => b.length - a.length)) {
  if (args.name.startsWith(`${color}_`)) {
    variant = color;
    family = args.name.slice(color.length + 1);
    break;
  }
}
if (!variant && parts.length > 1) family = parts.slice(1).join("_");

const collection = block ? Object.values(mc.blocksByName ?? {}) : Object.values(mc.itemsByName ?? {});
const siblings = collection
  .filter((entry) => entry.name !== args.name)
  .filter((entry) => entry.name.endsWith(`_${family}`) || (block && entry.material === block.material))
  .map((entry) => ({ id: entry.name, display_name: entry.displayName }))
  .slice(0, 128);

const output = {
  schema_version: 1,
  target: {
    id: args.name,
    display_name: entity.displayName,
    edition: "java",
    version: String(args.version),
    kind,
    family,
    ...(variant ? { variant } : {})
  },
  facts,
  sibling_candidates: siblings,
  notes: [
    "This file contains structured facts only. Add version-specific contextual facts from Minecraft Wiki before writing clues.",
    "Facts with verified=false require a second source before use."
  ]
};

const json = `${JSON.stringify(output, null, 2)}\n`;
if (args.out) fs.writeFileSync(args.out, json, "utf8");
else process.stdout.write(json);

