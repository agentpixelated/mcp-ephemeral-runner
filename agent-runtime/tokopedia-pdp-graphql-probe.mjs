#!/usr/bin/env node
import { readFile } from 'node:fs/promises';

const inputPath = process.argv[2] || 'agent-runtime/tokopedia-pdp-graphql-request.json';
const input = JSON.parse(await readFile(inputPath, 'utf8'));
const querySourceUrl = 'https://raw.githubusercontent.com/pdcgo/tokopedia_lib/bb2e107f47642c7c7ea80da274eb42e36ac03015/lib/query/pdp_get_layout_query.go';

const source = await (await fetch(querySourceUrl, { signal: AbortSignal.timeout(15000) })).text();
const marker = 'PdpGetLayoutQuery = `';
const start = source.indexOf(marker);
if (start < 0) throw new Error('PDP query marker not found');
const qStart = start + marker.length;
const qEnd = source.indexOf('\n\t`', qStart);
if (qEnd < 0) throw new Error('PDP query terminator not found');
const query = source.slice(qStart, qEnd);

const variables = {
  shopDomain: input.shopDomain,
  productKey: input.productKey,
  layoutID: '',
  apiVersion: 1,
  extParam: '',
};

const res = await fetch('https://gql.tokopedia.com/graphql/PDPGetLayoutQuery', {
  method: 'POST',
  headers: {
    'content-type': 'application/json',
    'origin': 'https://www.tokopedia.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'x-tkpd-akamai': 'pdpGetLayout',
    'x-device': 'desktop',
  },
  body: JSON.stringify({ operationName: 'PDPGetLayoutQuery', variables, query }),
  signal: AbortSignal.timeout(30000),
});
const text = await res.text();
let body;
try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 20000) }; }
console.log(JSON.stringify({ ok: res.ok, status: res.status, variables, body }, null, 2));
