# Baseline Comparison Results - Task 1 (Recent Constraint Tracking)

**Task:** 01_Recent_Constraint_Tracking_task_01_arxiv_csv_digest  
**Test Time:** 2025-04-25 13:35  
**Model:** kimi-k2.5

---

## Summary Table

| Method | Budget | Score | Status | Input Tokens | Output Tokens | Total Tokens | Context Reduction | Compression Ratio |
|--------|--------|-------|--------|--------------|---------------|--------------|-------------------|-------------------|
| full-context | 200K | **0.2177** | ✓ ok | 4,713 | 734 | 5,447 | 0.00% | 1.00× |
| sliding-window | 12K | 0.1960 | ✓ ok | 4,593 | 405 | 4,998 | 12.94% | 1.15× |
| lcm-proxy | 12K | **0.2081** | ✓ ok | 3,878 | 766 | 4,644 | **18.51%** | 1.17× |
| hierarchical | 12K | 0.2077 | ✓ ok | **2,031** | **513** | **2,544** | **73.31%** | **2.14×** |
| keyword | 12K | 0.1723 | ⚠ timeout | - | - | - | - | - |
| recursive-summary | 12K | 0.1723 | ⚠ timeout | - | - | - | - | - |

---

## Analysis

### 1. Accuracy (Overall Score)

| Rank | Method | Score | vs Full-Context |
|------|--------|-------|-----------------|
| 1 | **full-context** | **0.2177** | - |
| 2 | **lcm-proxy** | **0.2081** | -4.4% |
| 3 | hierarchical | 0.2077 | -4.6% |
| 4 | sliding-window | 0.1960 | -10.0% |
| 5 | keyword | 0.1723 | -20.9% |
| 5 | recursive-summary | 0.1723 | -20.9% |

**Key Insight:**
- **lcm-proxy** achieves the best accuracy among compressed methods, only 4.4% lower than full-context
- **hierarchical** also performs well with 73% context reduction but only 4.6% accuracy drop
- **keyword** and **recursive-summary** both timed out, resulting in fallback scores

### 2. Token Efficiency

| Rank | Method | Total Tokens | vs Full-Context | Savings |
|------|--------|--------------|-----------------|---------|
| 1 | **hierarchical** | **2,544** | -53.3% | **2,903** tokens |
| 2 | lcm-proxy | 4,644 | -14.7% | 803 tokens |
| 3 | sliding-window | 4,998 | -8.2% | 449 tokens |
| 4 | full-context | 5,447 | - | - |

**Key Insight:**
- **hierarchical** achieves the best token efficiency with 53% token reduction
- With only 2,544 total tokens vs 5,447 for full-context, it provides significant cost savings

### 3. Compression Effectiveness

| Rank | Method | Reduction Ratio | Raw → Compressed |
|------|--------|-----------------|------------------|
| 1 | **hierarchical** | **73.31%** | 13,277 → 3,543 chars |
| 2 | lcm-proxy | 18.51% | 12,189 → 9,933 chars |
| 3 | sliding-window | 12.94% | 13,777 → 11,994 chars |
| 4 | full-context | 0.00% | 12,189 → 12,189 chars |

**Key Insight:**
- **hierarchical** compression achieves the highest compression ratio (73%), significantly reducing context size
- This aggressive compression explains its low token usage while maintaining competitive accuracy

### 4. Best Methods by Use Case

| Use Case | Recommended Method | Reason |
|----------|-------------------|--------|
| **Maximum Accuracy** | full-context | Highest score (0.2177) but most expensive |
| **Best Accuracy/Efficiency Balance** | **lcm-proxy** | 96% of full-context accuracy with 18% compression |
| **Maximum Cost Savings** | **hierarchical** | 53% token reduction with only 4.6% accuracy loss |
| **Reliable Execution** | sliding-window | Simple, stable, no timeouts |

---

## Detailed Results

### full-context (Baseline)
- **Score:** 0.2177
- **Status:** ok
- **Input Tokens:** 4,713
- **Output Tokens:** 734
- **Total Tokens:** 5,447
- **Raw Context:** 12,189 chars
- **Compressed Context:** 12,189 chars
- **Reduction:** 0.00%

### sliding-window
- **Score:** 0.1960
- **Status:** ok
- **Input Tokens:** 4,593
- **Output Tokens:** 405
- **Total Tokens:** 4,998
- **Raw Context:** 13,777 chars
- **Compressed Context:** 11,994 chars
- **Reduction:** 12.94%

### lcm-proxy
- **Score:** 0.2081
- **Status:** ok
- **Input Tokens:** 3,878
- **Output Tokens:** 766
- **Total Tokens:** 4,644
- **Raw Context:** 12,189 chars
- **Compressed Context:** 9,933 chars
- **Reduction:** 18.51%

### hierarchical
- **Score:** 0.2077
- **Status:** ok
- **Input Tokens:** 2,031
- **Output Tokens:** 513
- **Total Tokens:** 2,544
- **Raw Context:** 13,277 chars
- **Compressed Context:** 3,543 chars
- **Reduction:** 73.31%

### keyword
- **Score:** 0.1723
- **Status:** ok_fallback (API timeout)
- **Error:** ReadTimeout - API call exceeded 90s timeout

### recursive-summary
- **Score:** 0.1723
- **Status:** ok_fallback (API timeout)
- **Error:** ReadTimeout - API call exceeded 90s timeout

---

## Conclusions

1. **lcm-proxy** is the best overall method for this task, achieving near-full-context accuracy (0.2081 vs 0.2177) with moderate compression (18.5%)

2. **hierarchical** offers the best cost-efficiency tradeoff, cutting token usage in half while maintaining ~95% of baseline accuracy

3. **keyword** and **recursive-summary** methods suffered from API timeouts, suggesting they may be too complex for this specific task configuration

4. The task's constraint-heavy nature (tracking year ranges, topic filters, CSV schemas) benefits from methods that preserve structured information

5. **Recommendation:** For production use, start with **lcm-proxy** for balanced performance, or **hierarchical** if cost is the primary concern
