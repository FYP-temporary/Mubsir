# MUBSIR — Final Stealth Rule Validation

## 1. Selected Configuration

- Formula: A — Historical P95-Based
- Configuration: Balanced
- High multiplier: 0.25
- Medium multiplier: 0.50
- Low multiplier: 0.75
- Minimum added events: 1
- Applies to EMAIL, USB, and HTTP

## 2. Validation Results

- Observations: 100,585
- Users: 936
- Strict level separation: 91.01%
- All levels equal: 1.94%
- Formula and integer-count checks: PASS
- Channel-level checks: PASS
- Previous evidence reconciliation: PASS

## 3. Channel-Level Results

| channel | level | observations | users | multiplier | median_added | p95_added | strict_separation_pct | all_equal_pct | strict_N1_pct | new_P95_pct | final_P95_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EMAIL | High | 57815 | 936 | 0.25 | 1.0 | 2.0 | 89.96 | 3.28 | 79.28 | 15.14 | 18.67 |
| EMAIL | Medium | 57815 | 936 | 0.5 | 2.0 | 4.0 | 89.96 | 3.28 | 79.28 | 32.54 | 36.07 |
| EMAIL | Low | 57815 | 936 | 0.75 | 3.0 | 5.0 | 89.96 | 3.28 | 79.28 | 67.06 | 70.6 |
| USB | High | 29612 | 690 | 0.25 | 1.0 | 3.0 | 92.07 | 0.18 | 83.72 | 15.79 | 19.64 |
| USB | Medium | 29612 | 690 | 0.5 | 2.0 | 5.0 | 92.07 | 0.18 | 83.72 | 42.0 | 45.85 |
| USB | Low | 29612 | 690 | 0.75 | 3.0 | 8.0 | 92.07 | 0.18 | 83.72 | 81.72 | 85.57 |
| HTTP | High | 13158 | 533 | 0.25 | 1.0 | 4.0 | 93.22 | 0.0 | 87.6 | 18.57 | 22.35 |
| HTTP | Medium | 13158 | 533 | 0.5 | 2.0 | 8.0 | 93.22 | 0.0 | 87.6 | 50.78 | 54.56 |
| HTTP | Low | 13158 | 533 | 0.75 | 3.0 | 12.0 | 93.22 | 0.0 | 87.6 | 90.58 | 94.36 |

## 4. Limitations

- Validation uses hypothetical injection-count calculations.
- Low Stealth introduces substantial new P95 exceedances,
  particularly in USB and HTTP.
- Strict level separation is not guaranteed for every observation.
- Final scenario scheduling and injection feasibility are pending.
- Model detection performance has not been evaluated.

## 5. Handoff

- Use selected_injection_rule.json in subsequent notebooks.
- Preserve historical baseline statistics.
- No actual attack injection was performed.
