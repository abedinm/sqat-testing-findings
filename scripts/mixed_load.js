// mixed_load.js - Arm C, the variance-injection arm.
//
// Every other arm in this study varies UNIFORM cost: a bigger dataset, a deeper queue.
// In those, every request slows by roughly the same factor, and the mean tracks the
// slowdown faithfully. This arm holds the *work* constant and varies only its
// DISTRIBUTION, which is the condition the paper's central claim is actually about.
//
// It does so without modifying the application at all: it mixes two real endpoints in a
// known proportion.
//
//   /robots.txt   - 110 bytes, no file read of content.json, no JSON.parse  (cheap)
//   /api/content  - 87 KB, readFile + JSON.parse per request                (expensive)
//
// A 99/1 mix contains exactly the same expensive work as a 1%-sampled slow path in a real
// service. The mean is dominated by the cheap majority; the p99 sits on the expensive
// minority. Comparing that against a 100%-expensive workload separates "slow" from
// "variable", which is the distinction the paper argues the mean cannot express.
//
// Env:
//   MIX       "99:/robots.txt,1:/api/content"   weight:path pairs, weights are relative
//   VUS       default 8      (the calibrated knee)
//   DURATION  default 120s

import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8099';

function parseMix(spec) {
  const out = [];
  let total = 0;
  for (const part of spec.split(',')) {
    const idx = part.indexOf(':');
    const w = Number(part.slice(0, idx).trim());
    const path = part.slice(idx + 1).trim();
    if (!(w > 0) || !path) throw new Error(`bad mix entry: ${part}`);
    total += w;
    out.push({ w, path, cum: total });
  }
  return { entries: out, total };
}

const MIX = parseMix(__ENV.MIX || '99:/robots.txt,1:/api/content');

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 8),
      duration: __ENV.DURATION || '120s',
      gracefulStop: '5s',
    },
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  discardResponseBodies: true,
};

export default function () {
  // Deterministic-in-aggregate weighted pick. Per-request randomness is what creates the
  // variance being studied, so it is intentional and not a source of bias: over a 120 s
  // run each route's share converges on its weight.
  const r = Math.random() * MIX.total;
  let chosen = MIX.entries[MIX.entries.length - 1].path;
  for (const e of MIX.entries) {
    if (r <= e.cum) { chosen = e.path; break; }
  }
  const res = http.get(`${BASE}${chosen}`, { tags: { route: chosen } });
  check(res, { 'status is 200': (r2) => r2.status === 200 });
}

export function handleSummary(data) {
  const m = data.metrics;
  const d = m.http_req_duration ? m.http_req_duration.values : {};
  const out = {
    label: __ENV.LABEL || 'mixed',
    mix: __ENV.MIX || '99:/robots.txt,1:/api/content',
    vus: Number(__ENV.VUS || 8),
    duration: __ENV.DURATION || '120s',
    generated_at: new Date().toISOString(),
    requests: m.http_reqs ? m.http_reqs.values.count : 0,
    rps: m.http_reqs ? m.http_reqs.values.rate : 0,
    failed_rate: m.http_req_failed ? m.http_req_failed.values.rate : 0,
    p50: d.med, avg: d.avg, p90: d['p(90)'], p95: d['p(95)'], p99: d['p(99)'],
    min: d.min, max: d.max,
    metrics: m,
  };
  const res = {};
  res[__ENV.SUMMARY || 'results/mixed/summary.json'] = JSON.stringify(out, null, 2);
  res['stdout'] =
    `  mix=${out.mix.padEnd(34)} reqs=${String(out.requests).padStart(7)} ` +
    `rps=${out.rps.toFixed(0).padStart(6)} mean=${fmt(out.avg)} p50=${fmt(out.p50)} ` +
    `p95=${fmt(out.p95)} p99=${fmt(out.p99)} max=${fmt(out.max)} ` +
    `p99/mean=${(out.p99 / out.avg).toFixed(2)}\n`;
  return res;
}

function fmt(v) { return v === undefined ? 'n/a' : v.toFixed(3).padStart(9); }
