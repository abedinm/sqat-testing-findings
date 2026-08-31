// open_load.js - Arm E, the coordinated-omission control.
//
// WHY THIS ARM EXISTS
// Every percentile in Stages 2, 3, 5, 6 and 7 came from k6's constant-vus executor, which
// is a CLOSED model: a VU issues its next request only after the previous one returns.
// k6's own documentation states that when the system "starts to respond more slowly, a
// closed model load test will wait, resulting in increased iteration durations and a
// tapering off of the arrival rate", and that "in some testing literature, this problem is
// known as coordinated omission."
//
// Coordinated omission biases percentiles OPTIMISTICALLY: requests that would have been
// issued during a slow period are never issued, so the slow period is under-sampled.
// A study whose central claim is "percentiles reveal what the mean hides" cannot leave
// that unmeasured, because it attacks the very statistic the argument rests on.
//
// This arm re-measures the same route with constant-arrival-rate (an OPEN model executor):
// iterations start on a fixed schedule regardless of how slowly the server responds.
// Comparing the two at matched throughput quantifies the coordinated-omission bias in this
// study's own numbers.
//
// Env: RATE (req/s), DURATION, ROUTE, MAX_VUS

import http from 'k6/http';
import { check } from 'k6';

const BASE = __ENV.BASE || 'http://127.0.0.1:8099';
const ROUTE = __ENV.ROUTE || '/api/content';

export const options = {
  scenarios: {
    open: {
      executor: 'constant-arrival-rate',
      rate: Number(__ENV.RATE || 1100),
      timeUnit: '1s',
      duration: __ENV.DURATION || '120s',
      preAllocatedVUs: Number(__ENV.PRE_VUS || 200),
      maxVUs: Number(__ENV.MAX_VUS || 3000),
      gracefulStop: '10s',
    },
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  discardResponseBodies: true,
};

export default function () {
  const res = http.get(`${BASE}${ROUTE}`);
  check(res, { 'status is 200': (r) => r.status === 200 });
}

export function handleSummary(data) {
  const m = data.metrics;
  const d = m.http_req_duration ? m.http_req_duration.values : {};
  const out = {
    label: __ENV.LABEL || 'open',
    route: ROUTE,
    target_rate: Number(__ENV.RATE || 1100),
    duration: __ENV.DURATION || '120s',
    generated_at: new Date().toISOString(),
    requests: m.http_reqs ? m.http_reqs.values.count : 0,
    rps: m.http_reqs ? m.http_reqs.values.rate : 0,
    // dropped_iterations is the honest signal that the generator could not keep the
    // schedule - i.e. that offered load exceeded what the system could absorb.
    dropped_iterations: m.dropped_iterations ? m.dropped_iterations.values.count : 0,
    failed_rate: m.http_req_failed ? m.http_req_failed.values.rate : 0,
    p50: d.med, avg: d.avg, p90: d['p(90)'], p95: d['p(95)'], p99: d['p(99)'],
    min: d.min, max: d.max,
    metrics: m,
  };
  const res = {};
  res[__ENV.SUMMARY || 'results/open/summary.json'] = JSON.stringify(out, null, 2);
  res['stdout'] =
    `  rate=${String(out.target_rate).padStart(5)}/s achieved=${out.rps.toFixed(0).padStart(6)} ` +
    `dropped=${String(out.dropped_iterations).padStart(7)} mean=${fmt(out.avg)} p50=${fmt(out.p50)} ` +
    `p95=${fmt(out.p95)} p99=${fmt(out.p99)} fail=${(out.failed_rate * 100).toFixed(2)}%\n`;
  return res;
}

function fmt(v) { return v === undefined ? 'n/a' : v.toFixed(3).padStart(9); }
