# Writing worksheet

Every number below came out of a run and is already verified. The headings, tables and
figures are fixed and stay where they are. The prose is the part you write.

How to use it: read the numbers for a section, look at the figure it names, then write
what you measured and what it means. Two or three sentences per box is usually enough.
Do not put adjectives on numbers. If a result surprised you, write that down, because
the surprises are the interesting part of this study and a marker will notice them.

When a box is filled, paste it into paper/paper_template.md in place of the paragraph
that is there now, keeping the {{placeholders}} exactly as written. Then rebuild.

---

## Abstract

*roughly 340 words*

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 39.4 | `{{total_requests_m}}` | derived from the above |
| 188 | `{{dataset_records}}` | sut/data/content.json |
| 2.55 | `{{scaled_x1_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 1.13 | `{{scaled_x1000_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 4.2 | `{{soak_requests_m}}` | derived from the above |
| 0.9944 | `{{soak_degradation}}` | results/soak/metrics.json |
| 6.51 | `{{armc_mean_dilution_10}}` | derived from the above |
| 1.47 | `{{armc_p999_dilution_10}}` | derived from the above |
| 1.506 | `{{ladder_mix_0p1pct_p99}}` | results/mixed/percentile_ladder.json |
| 1.506 | `{{ladder_uniform_cheap_p99}}` | results/mixed/percentile_ladder.json |
| 52.8 | `{{armb_improvement_x}}` | derived from the above |
| 21.3 | `{{armb_p99_improvement_x}}` | derived from the above |
| 99.998 | `{{armb_enabled_failed_pct}}` | results/armb/enabled |

**Write here:**

> 


## 1. Introduction

*roughly 180 words*

**Write here:**

> 


### 1.1 Hypotheses

*roughly 170 words*

**Write here:**

> 


### 1.2 Contributions

*roughly 110 words*

**Write here:**

> 


## 2. Background and Related Work

*roughly 420 words*

**Write here:**

> 


## 3. System Under Test

*roughly 220 words*

- Fig. 1 sits here: Request path through the application. Both request classes reach the same uncached read and parse.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 88,826 | `{{dataset_bytes}}` | sut/data/content.json |
| 188 | `{{dataset_records}}` | sut/data/content.json |

**Write here:**

> 


### 4.1 Environment

*roughly 90 words*

- Table 1 sits here: Test environment. System under test and load generator share one host.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| Intel Core i7-10700 (8 cores / 16 threads, 2.90 GHz base) | `{{host_cpu}}` | docs/environment.md |
| 32 | `{{host_ram_gb}}` | docs/environment.md |
| Windows 11 Pro, build 26200.9168 | `{{host_os}}` | docs/environment.md |
| 24.15.0 | `{{node_version}}` | docs/environment.md |
| 2.2.0 | `{{k6_version}}` | docs/environment.md |

**Write here:**

> 


### 4.2 Instrumentation and data handling

*roughly 100 words*

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 4,221,421 | `{{soak_requests}}` | results/soak/metrics.json |

**Write here:**

> 


### 4.3 Statistical treatment

*roughly 120 words*

**Write here:**

> 


### 4.4 Distinguishing server saturation from generator contention

*roughly 80 words*

**Write here:**

> 


### 4.5 Experimental arms

*roughly 60 words*

- Table 2 sits here: The six experimental arms and the variable each isolates.
- Fig. 2 sits here: Experimental design. Five arms vary uniform cost; only Arm C varies its distribution.

**Write here:**

> 


### 5.1 Calibration: the knee, and evidence that the server is the bottleneck

*roughly 200 words*

- Table 3 sits here: Tail divergence (p99/p50) across the calibration sweep.
- Fig. 3 sits here: Calibration sweep. Latency and tail divergence against concurrency; p99/p50 peaks near the knee and falls under heavy load.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 10 | `{{calib_levels}}` | results/calibration/sweep.csv |
| 200 | `{{calib_max_vus}}` | results/calibration/sweep.csv |
| 2,116 | `{{calib_peak_rps}}` | results/calibration/sweep.csv |
| 7.85 | `{{calib_p50_16}}` | results/calibration/sweep.csv |
| 94.35 | `{{calib_p50_200}}` | results/calibration/sweep.csv |
| 1.4 | `{{calib_cores_plateau}}` | results/calibration/sweep.csv |
| 1.95 | `{{calib_ratio_1}}` | results/calibration/sweep.csv |
| 2.18 | `{{calib_ratio_2}}` | results/calibration/sweep.csv |
| 3.85 | `{{calib_ratio_4}}` | results/calibration/sweep.csv |
| 3.47 | `{{calib_ratio_8}}` | results/calibration/sweep.csv |
| 2.32 | `{{calib_ratio_16}}` | results/calibration/sweep.csv |
| 1.17 | `{{calib_ratio_200}}` | results/calibration/sweep.csv |

**Write here:**

> 


### 5.2 Arm A: baseline load matrix

*roughly 80 words*

- Table 4 sits here: Arm A load matrix. 45 runs, zero failures, n = 4 per cell after warm-up discard.
- Fig. 4 sits here: Arm A. Absolute latency rises with load while the tail becomes relatively less extreme.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 9 | `{{matrix_warmups_discarded}}` | results/matrix/aggregate.json |
| 1,493 | `{{arma_services_html_v2_rps}}` | results/matrix/aggregate.json |
| 1.313 | `{{arma_services_html_v2_mean}}` | results/matrix/aggregate.json |
| 1.233 | `{{arma_services_html_v2_p50}}` | results/matrix/aggregate.json |
| 1.749 | `{{arma_services_html_v2_p95}}` | results/matrix/aggregate.json |
| 2.254 | `{{arma_services_html_v2_p99}}` | results/matrix/aggregate.json |
| 1.72 | `{{arma_services_html_v2_ratio}}` | results/matrix/aggregate.json |
| 1,030 | `{{arma_api_content_v2_rps}}` | results/matrix/aggregate.json |
| 1.935 | `{{arma_api_content_v2_mean}}` | results/matrix/aggregate.json |
| 1.788 | `{{arma_api_content_v2_p50}}` | results/matrix/aggregate.json |
| 2.442 | `{{arma_api_content_v2_p95}}` | results/matrix/aggregate.json |
| 8.952 | `{{arma_api_content_v2_p99}}` | results/matrix/aggregate.json |
| 4.63 | `{{arma_api_content_v2_ratio}}` | results/matrix/aggregate.json |
| 1,878 | `{{arma_sitemap_xml_v2_rps}}` | results/matrix/aggregate.json |
| +41 more in the template | | |

**Write here:**

> 


### 5.3 Stress: breaking point and failure mode

*roughly 180 words*

- Table 5 sits here: Stress test at the breaking point, with maxVUs raised to 20,000.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 2,066.5 | `{{stress_a_p50}}` | results/stress/summary.json |
| 5.856 | `{{stress_b_failed_pct}}` | results/stress_b/summary.json |
| 1,504 | `{{stress_b_rps}}` | results/stress_b/summary.json |
| 15 | `{{stress_b_p50}}` | results/stress_b/summary.json |
| 2,478 | `{{stress_b_p99}}` | results/stress_b/summary.json |
| 0 | `{{stress_b_5xx}}` | results/stress_b/summary.json |
| 8,296 | `{{stress_b_transport_err}}` | results/stress_b/summary.json |
| 301 | `{{stress_b_handles_start}}` | results/stress_b/server_proc.csv |
| 8,679 | `{{stress_b_handles_peak}}` | results/stress_b/server_proc.csv |
| 69 | `{{stress_b_rss_start}}` | results/stress_b/server_proc.csv |
| 779 | `{{stress_b_rss_peak}}` | results/stress_b/server_proc.csv |

**Write here:**

> 


### 5.4 Soak: H1 refuted

*roughly 110 words*

- Table 6 sits here: Soak test. One continuous 3600 s run at the calibrated knee.
- Fig. 5 sits here: Soak test. Binned mean and p99 across 3600 s; no trend is present.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 3,599 | `{{soak_span_s}}` | results/soak/metrics.json |
| 4,221,421 | `{{soak_requests}}` | results/soak/metrics.json |
| 0 | `{{soak_errors_pct}}` | results/soak/metrics.json |
| 6.814 | `{{soak_mean}}` | results/soak/metrics.json |
| 6.348 | `{{soak_p50}}` | results/soak/metrics.json |
| 8.895 | `{{soak_p95}}` | results/soak/metrics.json |
| 17.436 | `{{soak_p99}}` | results/soak/metrics.json |
| 19.769 | `{{soak_p999}}` | results/soak/metrics.json |
| 8.921 | `{{soak_early_p95}}` | results/soak/metrics.json |
| 8.871 | `{{soak_late_p95}}` | results/soak/metrics.json |
| 0.9944 | `{{soak_degradation}}` | results/soak/metrics.json |
| -0.56 | `{{soak_degradation_pct}}` | results/soak/metrics.json |
| 0 | `{{soak_mw_p}}` | results/soak/metrics.json |
| 0.0417 | `{{soak_effect_r}}` | results/soak/metrics.json |
| +2 more in the template | | |

**Write here:**

> 


### 5.5 Arm D: dataset scale, H2 refuted

*roughly 100 words*

- Table 7 sits here: Arm D. Response time against dataset size for /api/content at 8 VUs.
- Fig. 6 sits here: Arm D. Mean, p50 and p99 against dataset scale. All three rise together.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 5 | `{{scaled_x1_api_content_n}}` | results/scaled_merged/aggregate.json |
| 6.47 | `{{scaled_x1_api_content_mean}}` | results/scaled_merged/aggregate.json |
| 6.02 | `{{scaled_x1_api_content_p50}}` | results/scaled_merged/aggregate.json |
| 16.51 | `{{scaled_x1_api_content_p99}}` | results/scaled_merged/aggregate.json |
| 2.55 | `{{scaled_x1_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 1,236 | `{{scaled_x1_api_content_rps}}` | results/scaled_merged/aggregate.json |
| 5 | `{{scaled_x10_api_content_n}}` | results/scaled_merged/aggregate.json |
| 54.57 | `{{scaled_x10_api_content_mean}}` | results/scaled_merged/aggregate.json |
| 52.98 | `{{scaled_x10_api_content_p50}}` | results/scaled_merged/aggregate.json |
| 73.83 | `{{scaled_x10_api_content_p99}}` | results/scaled_merged/aggregate.json |
| 1.35 | `{{scaled_x10_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 146 | `{{scaled_x10_api_content_rps}}` | results/scaled_merged/aggregate.json |
| 5 | `{{scaled_x100_api_content_n}}` | results/scaled_merged/aggregate.json |
| 528.75 | `{{scaled_x100_api_content_mean}}` | results/scaled_merged/aggregate.json |
| +10 more in the template | | |

**Write here:**

> 


### 5.6 Arm C: variance injection, H4 tested

*roughly 420 words*

- Table 8 sits here: Arm C percentile ladder. Identical expensive work, redistributed across a varying fraction of requests.
- Fig. 7 sits here: Arm C. A slow path is invisible to any percentile below its own incidence.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 2,431,591 | `{{ladder_uniform_cheap_n}}` | results/mixed/percentile_ladder.json |
| 0.337 | `{{ladder_uniform_cheap_mean}}` | results/mixed/percentile_ladder.json |
| 0 | `{{ladder_uniform_cheap_p50}}` | results/mixed/percentile_ladder.json |
| 1.003 | `{{ladder_uniform_cheap_p90}}` | results/mixed/percentile_ladder.json |
| 1.506 | `{{ladder_uniform_cheap_p99}}` | results/mixed/percentile_ladder.json |
| 2 | `{{ladder_uniform_cheap_p999}}` | results/mixed/percentile_ladder.json |
| 6.535 | `{{ladder_uniform_cheap_p9999}}` | results/mixed/percentile_ladder.json |
| 0.041 | `{{ladder_uniform_cheap_frac_over_3ms}}` | results/mixed/percentile_ladder.json |
| 139,217 | `{{ladder_uniform_expensive_n}}` | results/mixed/percentile_ladder.json |
| 6.874 | `{{ladder_uniform_expensive_mean}}` | results/mixed/percentile_ladder.json |
| 6.386 | `{{ladder_uniform_expensive_p50}}` | results/mixed/percentile_ladder.json |
| 7.561 | `{{ladder_uniform_expensive_p90}}` | results/mixed/percentile_ladder.json |
| 17.177 | `{{ladder_uniform_expensive_p99}}` | results/mixed/percentile_ladder.json |
| 19.561 | `{{ladder_uniform_expensive_p999}}` | results/mixed/percentile_ladder.json |
| +29 more in the template | | |

**Write here:**

> 


### 5.7 Arm B: rate limiting, H3 confirmed

*roughly 390 words*

- Table 9 sits here: Arm B. /api/search measured with the rate limiter disabled and enabled.
- Fig. 8 sits here: Arm B. Every latency and throughput metric improves while the error rate reaches 100%.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 6 | `{{armb_disabled_n}}` | results/armb/disabled |
| 2 | `{{armb_enabled_n}}` | results/armb/enabled |
| 18.63 | `{{armb_disabled_mean}}` | results/armb/disabled |
| 0.353 | `{{armb_enabled_mean}}` | results/armb/enabled |
| 52.8 | `{{armb_improvement_x}}` | derived from the above |
| 17.609 | `{{armb_disabled_p50}}` | results/armb/disabled |
| 0 | `{{armb_enabled_p50}}` | results/armb/enabled |
| 32.088 | `{{armb_disabled_p99}}` | results/armb/disabled |
| 1.505 | `{{armb_enabled_p99}}` | results/armb/enabled |
| 21.3 | `{{armb_p99_improvement_x}}` | derived from the above |
| 429 | `{{armb_disabled_rps}}` | results/armb/disabled |
| 20,128 | `{{armb_enabled_rps}}` | results/armb/enabled |
| 46.9 | `{{armb_rps_x}}` | derived from the above |
| 0 | `{{armb_disabled_failed_pct}}` | results/armb/disabled |
| +1 more in the template | | |

**Write here:**

> 


### 5.8 Arm E: coordinated-omission control

*roughly 220 words*

- Table 10 sits here: Arm E. Open-model measurement of /api/content at three offered rates.
- Fig. 9 sits here: Arm E. An open-model test exposes a saturation cliff a closed-model test cannot produce.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 600 | `{{arme_600_achieved}}` | results/open/index.csv |
| 0 | `{{arme_600_dropped}}` | results/open/index.csv |
| 1.104 | `{{arme_600_mean}}` | results/open/index.csv |
| 4.182 | `{{arme_600_p95}}` | results/open/index.csv |
| 10.274 | `{{arme_600_p99}}` | results/open/index.csv |
| 1,099 | `{{arme_1100_achieved}}` | results/open/index.csv |
| 0 | `{{arme_1100_dropped}}` | results/open/index.csv |
| 4.544 | `{{arme_1100_mean}}` | results/open/index.csv |
| 11.254 | `{{arme_1100_p95}}` | results/open/index.csv |
| 36.685 | `{{arme_1100_p99}}` | results/open/index.csv |
| 1,158 | `{{arme_1400_achieved}}` | results/open/index.csv |
| 26,226 | `{{arme_1400_dropped}}` | results/open/index.csv |
| 2,276.513 | `{{arme_1400_mean}}` | results/open/index.csv |
| 2,664.987 | `{{arme_1400_p95}}` | results/open/index.csv |
| +5 more in the template | | |

**Write here:**

> 


### 5.9 Percentile sampling bias

*roughly 70 words*

- Table 11 sits here: Percentile sampling bias: raw request samples against time-quantized samples.

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 1.888 | `{{smoke_p99_raw}}` | results/smoke/metrics.json |
| 1.041 | `{{smoke_p99_quant}}` | results/smoke/metrics.json |
| 0.847 | `{{smoke_bias}}` | results/smoke/metrics.json |
| 17.436 | `{{soak_p99_raw}}` | results/soak/metrics.json |
| 7.26 | `{{soak_p99_quant}}` | results/soak/metrics.json |
| 10.176 | `{{soak_bias}}` | results/soak/metrics.json |

**Write here:**

> 


### 6.1 The mean conceals variance, not slowness

*roughly 160 words*

**Write here:**

> 


### 6.2 Percentiles matter most before a system looks broken

*roughly 70 words*

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 3.85 | `{{calib_ratio_4}}` | results/calibration/sweep.csv |
| 1.17 | `{{calib_ratio_200}}` | results/calibration/sweep.csv |

**Write here:**

> 


### 6.3 No latency statistic survives without an error rate

*roughly 90 words*

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 99.998 | `{{armb_enabled_failed_pct}}` | results/armb/enabled |

**Write here:**

> 


### 6.4 Implications for practice

*roughly 60 words*

**Write here:**

> 


## 7. Threats to Validity

*roughly 300 words*

**Write here:**

> 


## 8. Conclusion

*roughly 260 words*

Numbers to use, already verified:

| value | placeholder | measured in |
|-|-|-|
| 2.55 | `{{scaled_x1_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 1.13 | `{{scaled_x1000_api_content_ratio}}` | results/scaled_merged/aggregate.json |
| 4.2 | `{{soak_requests_m}}` | derived from the above |
| 0.9944 | `{{soak_degradation}}` | results/soak/metrics.json |
| 6.51 | `{{armc_mean_dilution_10}}` | derived from the above |
| 1.47 | `{{armc_p999_dilution_10}}` | derived from the above |
| 52.8 | `{{armb_improvement_x}}` | derived from the above |
| 21.3 | `{{armb_p99_improvement_x}}` | derived from the above |
| 99.998 | `{{armb_enabled_failed_pct}}` | results/armb/enabled |

**Write here:**

> 


## Acknowledgment

*roughly 110 words*

**Write here:**

> 


## References

*roughly 180 words*

**Write here:**

> 


## Appendix A, Reproducibility

*roughly 100 words*

**Write here:**

> 
