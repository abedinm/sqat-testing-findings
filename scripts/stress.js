// stress.js - Stage 4. Ramp offered load until the app breaks.
//
// Uses ramping-arrival-rate rather than ramping VUs. Calibration showed the server
// saturates at ~1,950-2,100 req/s, after which added VUs only lengthen the queue. Driving
// ARRIVAL RATE past service rate is the direct way to find the breaking point, and it
// expresses the answer in req/s - a property of the server - rather than in VU count,
// which is a property of the test harness.
//
// Aborts when either stop condition in the brief is met:
//   error rate > 5%   or   response time > 10 s

import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const BASE = __ENV.BASE || 'http://127.0.0.1:8099';
const ROUTE = __ENV.ROUTE || '/services.html';

const errNonHttp = new Counter('err_transport');
const err5xx = new Counter('err_5xx');
const err429 = new Counter('err_429');

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-arrival-rate',
      startRate: 500,
      timeUnit: '1s',
      preAllocatedVUs: 200,
      maxVUs: Number(__ENV.MAX_VUS || 4000),
      stages: [
        { target: 1000, duration: '30s' },
        { target: 2000, duration: '30s' },
        { target: 3000, duration: '30s' },
        { target: 4000, duration: '30s' },
        { target: 6000, duration: '30s' },
        { target: 8000, duration: '30s' },
        { target: 12000, duration: '30s' },
      ],
      gracefulStop: '10s',
    },
  },
  thresholds: {
    http_req_failed: [{ threshold: 'rate<0.05', abortOnFail: true, delayAbortEval: '10s' }],
    http_req_duration: [{ threshold: 'p(99)<10000', abortOnFail: true, delayAbortEval: '10s' }],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  discardResponseBodies: true,
};

export default function () {
  const res = http.get(`${BASE}${ROUTE}`);
  check(res, { 'status is 200': (r) => r.status === 200 });
  if (res.status === 0) errNonHttp.add(1, { msg: res.error_code ? String(res.error_code) : 'unknown' });
  else if (res.status === 429) err429.add(1);
  else if (res.status >= 500) err5xx.add(1);
}

export function handleSummary(data) {
  const m = data.metrics;
  const d = m.http_req_duration ? m.http_req_duration.values : {};
  const out = {
    label: __ENV.LABEL || 'stress',
    route: ROUTE,
    generated_at: new Date().toISOString(),
    requests: m.http_reqs ? m.http_reqs.values.count : 0,
    rps_achieved: m.http_reqs ? m.http_reqs.values.rate : 0,
    dropped_iterations: m.dropped_iterations ? m.dropped_iterations.values.count : 0,
    failed_rate: m.http_req_failed ? m.http_req_failed.values.rate : 0,
    err_transport: m.err_transport ? m.err_transport.values.count : 0,
    err_5xx: m.err_5xx ? m.err_5xx.values.count : 0,
    err_429: m.err_429 ? m.err_429.values.count : 0,
    p50: d.med, avg: d.avg, p95: d['p(95)'], p99: d['p(99)'], max: d.max,
    metrics: m,
  };
  const res = {};
  res[__ENV.SUMMARY || 'results/stress/summary.json'] = JSON.stringify(out, null, 2);
  res['stdout'] =
    `\nSTRESS  requests=${out.requests}  achieved=${out.rps_achieved.toFixed(0)}/s  ` +
    `dropped_iters=${out.dropped_iterations}\n` +
    `  failed=${(out.failed_rate * 100).toFixed(2)}%  transport_err=${out.err_transport}  ` +
    `5xx=${out.err_5xx}  429=${out.err_429}\n` +
    `  p50=${fmt(out.p50)} p95=${fmt(out.p95)} p99=${fmt(out.p99)} max=${fmt(out.max)}\n`;
  return res;
}

function fmt(v) { return v === undefined ? 'n/a' : v.toFixed(1); }
