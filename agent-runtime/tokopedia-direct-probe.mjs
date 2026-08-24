#!/usr/bin/env node
const params = new URLSearchParams({
  device: 'desktop',
  enter_method: 'normal_search',
  l_name: 'sre',
  navsource: '',
  ob: '3',
  page: '1',
  q: 'iphone 11 second',
  pmin: '',
  pmax: '3000000',
  related: 'true',
  rows: '10',
  safe_search: 'false',
  scheme: 'https',
  show_adult: 'false',
  source: 'search',
  srp_component_id: '02.01.00.00',
  st: 'product',
  start: '0',
  topads_bucket: 'true',
  unique_id: Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2),
  variants: '',
});

const query = `query SearchProductV5Query($params: String!) {
  searchProductV5(params: $params) {
    header { totalData responseCode keywordProcess }
    data {
      products {
        id: id_str_auto_
        name
        url
        rating
        price { text number }
        shop { name city tier }
      }
    }
  }
}`;

const url = 'https://gql.tokopedia.com/graphql/SearchProductV5Query';
const headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/139 Safari/537.36',
  'Accept': '*/*',
  'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
  'Content-Type': 'application/json',
  'Origin': 'https://www.tokopedia.com',
  'Referer': 'https://www.tokopedia.com/',
  'X-Source': 'tokopedia-lite',
  'X-Version': '1.0',
};

try {
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({ operationName: 'SearchProductV5Query', query, variables: { params: params.toString() } }),
    signal: AbortSignal.timeout(30000),
  });
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 2000) }; }
  console.log(JSON.stringify({ ok: res.ok, status: res.status, body }, null, 2));
} catch (error) {
  console.log(JSON.stringify({ ok: false, error: String(error?.stack || error) }, null, 2));
}
