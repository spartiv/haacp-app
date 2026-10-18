// Generates src/api/schema.gen.ts from the backend's OpenAPI spec.
// Usage: npm run gen:api
//
// Post-processing: the backend's recursive `JSONValue-Input/Output` schemas (used in
// audit-history snapshots) come out as self-referencing index-access types, which
// TypeScript rejects (TS2502). They are replaced with a top-level recursive alias.
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import openapiTS, { astToString } from 'openapi-typescript'

const specPath = fileURLToPath(new URL('../../handoff/openapi.json', import.meta.url))
const outPath = fileURLToPath(new URL('../src/api/schema.gen.ts', import.meta.url))

const spec = JSON.parse(readFileSync(specPath, 'utf8'))
let output = astToString(await openapiTS(spec))

const recursiveJson = /("JSONValue-(?:Input|Output)"): string \| number \| boolean \| \{[\s\S]*?\| null;/g
const replaced = output.match(recursiveJson)?.length ?? 0
if (replaced !== 2) {
  throw new Error(`Expected 2 JSONValue definitions to patch, found ${replaced}. Check the spec.`)
}
output = output.replace(recursiveJson, '$1: JsonValue;')

const header = `/**
 * Generated from handoff/openapi.json by scripts/gen-api.mjs — do not edit by hand.
 */

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };

`
writeFileSync(outPath, header + output)
console.log(`Wrote ${outPath}`)
