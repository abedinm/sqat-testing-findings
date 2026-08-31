// const_load.js - constant-VU load against one route.
// Used for calibration (Stage 2) and the load matrix (Stage 3/6).
//
// Env:
//   BASE      default http://127.0.0.1:8099   (localhost only, by design)
//   ROUTE     default /services.html
//   VUS       default 1
//   DURATION  default 30s
//   SUMMARY   path for the JSON summary
//   LABEL     run label recorded in the summary
//
// Constant VUs rather than a ramp: a ramp mixes warm-up with steady state, which blurs
// exactly the knee this study is trying to locate.

import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8099';
const ROUTE = __ENV.ROUTE || '/services.html';

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-vus',
      vus: Number(__ENV.VUS || 1),
      duration: __ENV.DURATION || '30s',
      gracefulStop: '5s',
    },
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  discardResponseBodies: __ENV.KEEP_BODIES === 'true' ? false : true,
};

export default function () {
  const res = http.get(`${BASE}${ROUTE}`);
  check(res, { 'status is 200': (r) => r.status === 200 });
}

export function handleSummary(data) {
  const m = data.metrics;
  const d = m.http_req_duration ? m.http_req_duration.values : {};
  const out = {
    label: __ENV.LABEL || 'run',
    route: ROUTE,
    vus: Number(__ENV.VUS || 1),
    duration: __ENV.DURATION || '30s',
    generated_at: new Date().toISOString(),
    requests: m.http_reqs ? m.http_reqs.values.count : 0,
    rps: m.http_reqs ? m.http_reqs.values.rate : 0,
    failed_rate: m.http_req_failed ? m.http_req_failed.values.rate : 0,
    p50: d.med, avg: d.avg, p90: d['p(90)'], p95: d['p(95)'], p99: d['p(99)'],
    min: d.min, max: d.max,
    metrics: m,
  };
  const res = {};
  res[__ENV.SUMMARY || 'results/run/summary.json'] = JSON.stringify(out, null, 2);
  res['stdout'] =
    `  VUS=${out.vus.toString().padStart(3)}  reqs=${String(out.requests).padStart(7)}  ` +
    `rps=${out.rps.toFixed(0).padStart(6)}  fail=${(out.failed_rate * 100).toFixed(2)}%  ` +
    `p50=${fmt(out.p50)}  p95=${fmt(out.p95)}  p99=${fmt(out.p99)}  max=${fmt(out.max)}\n`;
  return res;
}

function fmt(v) {
  return v === undefined ? 'n/a' : v.toFixed(2).padStart(8);
}
