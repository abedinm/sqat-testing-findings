// smoke.js - Task 4 validation.
// One route, 1 virtual user, 30 seconds. Purpose is not to stress anything: it is to
// prove the pipeline produces real response-time data and that the app does not error
// under trivial load.
//
// localhost only. BASE is fixed to 127.0.0.1 by design - this study never touches a
// public hostname.

import http from 'k6/http';
import { check } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE = __ENV.BASE || 'http://127.0.0.1:8099';
const ROUTE = __ENV.ROUTE || '/services.html';

export const options = {
  vus: 1,
  duration: __ENV.DURATION || '30s',
  // No thresholds that abort: a smoke run must report what happened, not stop early.
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const ttfb = new Trend('ttfb_ms', true);
const failures = new Rate('route_failures');

export default function () {
  const res = http.get(`${BASE}${ROUTE}`);
  const ok = check(res, {
    'status is 200': (r) => r.status === 200,
    'body is non-empty': (r) => r.body && r.body.length > 0,
  });
  failures.add(!ok);
  ttfb.add(res.timings.waiting);
}

export function handleSummary(data) {
  const out = {
    label: __ENV.LABEL || 'smoke',
    route: ROUTE,
    base: BASE,
    vus: options.vus,
    duration: options.duration,
    generated_at: new Date().toISOString(),
    metrics: data.metrics,
  };
  const path = __ENV.SUMMARY || 'results/smoke/summary.json';
  const res = {};
  res[path] = JSON.stringify(out, null, 2);
  res['stdout'] = textSummary(data);
  return res;
}

// Minimal text summary - avoids depending on a remote jslib import (no outbound network).
function textSummary(data) {
  const m = data.metrics;
  const d = m.http_req_duration ? m.http_req_duration.values : {};
  const reqs = m.http_reqs ? m.http_reqs.values.count : 0;
  const rate = m.http_reqs ? m.http_reqs.values.rate : 0;
  const failed = m.http_req_failed ? m.http_req_failed.values.rate : 0;
  const lines = [
    '',
    '================ SMOKE RESULT ================',
    `  route              ${ROUTE}`,
    `  requests           ${reqs}  (${rate.toFixed(2)}/s)`,
    `  http_req_failed    ${(failed * 100).toFixed(3)} %`,
    '  -- response time (ms) --',
    `  min                ${fmt(d.min)}`,
    `  p50 (med)          ${fmt(d.med)}`,
    `  avg                ${fmt(d.avg)}`,
    `  p90                ${fmt(d['p(90)'])}`,
    `  p95                ${fmt(d['p(95)'])}`,
    `  p99                ${fmt(d['p(99)'])}`,
    `  max                ${fmt(d.max)}`,
    '==============================================',
    '',
  ];
  return lines.join('\n');
}

function fmt(v) {
  return v === undefined ? 'n/a' : v.toFixed(3);
}
