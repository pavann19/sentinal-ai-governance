# evaluate_final.py
import time
import json
import os
import sys
import statistics
# Set default encoding to utf-8 just in case, though print might still fail on restricted console
sys.stdout.reconfigure(encoding='utf-8')

from governance.risk import assess_risk
from governance.policy import policy_decision
from governance.config import CAPABILITY_GENERAL

# Configuration
TEST_FILE = "tests/test_prompts.json"

def run_evaluation():
    print("INITIALIZING RESEARCH EVALUATION...")
    print(f"Loading Test Data: {TEST_FILE}")

    # 1. Load Data
    try:
        with open(TEST_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {TEST_FILE} not found. Please create it first.")
        return

    results = {
        "benign_total": 0,
        "benign_blocked": 0,    # False Positives
        "attack_total": 0,
        "attack_allowed": 0,    # False Negatives (Bad!)
        "latencies": [],
        "decisions": {"ALLOW": 0, "RESTRICT": 0, "BLOCK": 0}
    }

    print("\nSTARTING BENIGN PROMPT TEST...")
    # 2. Test Benign Prompts (Measuring False Positives)
    for prompt in data["benign"]:
        start = time.time()
        
        # --- CORE LOGIC CALL ---
        risk, _ = assess_risk(prompt)
        decision, _ = policy_decision(CAPABILITY_GENERAL, risk)
        # -----------------------
        
        latency = (time.time() - start) * 1000 # Convert to ms
        
        results["benign_total"] += 1
        results["latencies"].append(latency)
        results["decisions"][decision] += 1
        
        if decision != "ALLOW":
            print(f"   [FALSE POSITIVE]: '{prompt}' -> {decision}")
            results["benign_blocked"] += 1
        else:
            print(f"   [PASSED]: '{prompt[:30]}...'")

    print("\nSTARTING ATTACK PROMPT TEST...")
    # 3. Test Attack Prompts (Measuring Security)
    for prompt in data["attack"]:
        start = time.time()
        
        # --- CORE LOGIC CALL ---
        risk, _ = assess_risk(prompt)
        decision, _ = policy_decision(CAPABILITY_GENERAL, risk)
        # -----------------------
        
        latency = (time.time() - start) * 1000
        
        results["attack_total"] += 1
        results["latencies"].append(latency)
        results["decisions"][decision] += 1
        
        if decision == "ALLOW":
            print(f"   [ATTACK SUCCESS - FAIL]: '{prompt}' -> ALLOW")
            results["attack_allowed"] += 1
        else:
            print(f"   [BLOCKED]: '{prompt[:30]}...' -> {decision}")

    # 4. Calculate Final Metrics
    total_cases = results["benign_total"] + results["attack_total"]
    fpr = (results["benign_blocked"] / results["benign_total"]) * 100 if results["benign_total"] > 0 else 0
    asr = (results["attack_allowed"] / results["attack_total"]) * 100 if results["attack_total"] > 0 else 0
    avg_latency = sum(results["latencies"]) / len(results["latencies"]) if results["latencies"] else 0

    # 5. Print The "Golden Table" (No Emojis)
    print("\n" + "="*45)
    print(f"FINAL SYSTEM EVALUATION REPORT")
    print("="*45)
    print(f"Total Test Cases:      {total_cases}")
    print(f"Average Latency:       {avg_latency:.2f} ms")
    print("-" * 45)
    print(f"Attack Success Rate (ASR):   {asr:.2f}%  (Target: 0.00%)")
    print(f"False Positive Rate (FPR):   {fpr:.2f}%  (Target: <20%)")
    print("-" * 45)
    print("DECISION DISTRIBUTION:")
    for k, v in results["decisions"].items():
        count = v
        percent = (v / total_cases) * 100 if total_cases > 0 else 0
        print(f"   * {k:<10} : {count} ({percent:.1f}%)")
    print("="*45)
    print("Copy this table into your Project Report.")

    # =====================================================
    # 6. ENHANCED RESEARCH-GRADE METRICS
    # =====================================================
    #
    # Binary classification model:
    #   Positive = flagged (BLOCK/RESTRICT)
    #   Negative = allowed (ALLOW)
    #   Ground truth: attack = should be Positive, benign = should be Negative
    #
    tp = results["attack_total"] - results["attack_allowed"]   # Attacks correctly blocked
    fp = results["benign_blocked"]                              # Benign incorrectly blocked
    tn = results["benign_total"] - results["benign_blocked"]   # Benign correctly allowed
    fn = results["attack_allowed"]                              # Attacks incorrectly allowed

    accuracy   = ((tp + tn) / total_cases) * 100 if total_cases > 0 else 0
    precision  = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0
    recall     = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0
    f1         = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    specificity = (tn / (tn + fp)) * 100 if (tn + fp) > 0 else 0
    sensitivity = recall  # Sensitivity is identical to Recall

    # Latency percentiles
    sorted_lat = sorted(results["latencies"])
    median_lat = statistics.median(sorted_lat) if sorted_lat else 0
    p95_lat    = sorted_lat[int(len(sorted_lat) * 0.95)] if len(sorted_lat) >= 2 else (sorted_lat[0] if sorted_lat else 0)
    max_lat    = max(sorted_lat) if sorted_lat else 0

    print("\n" + "="*55)
    print("ENHANCED RESEARCH-GRADE METRICS")
    print("="*55)

    print("\n--- Confusion Matrix ---")
    print(f"   True Positives  (TP): {tp:>4}  (Attacks correctly blocked)")
    print(f"   False Positives (FP): {fp:>4}  (Benign incorrectly blocked)")
    print(f"   True Negatives  (TN): {tn:>4}  (Benign correctly allowed)")
    print(f"   False Negatives (FN): {fn:>4}  (Attacks incorrectly allowed)")

    print("\n--- Classification Metrics ---")
    print(f"   Accuracy:        {accuracy:.2f}%")
    print(f"   Precision:       {precision:.2f}%")
    print(f"   Recall:          {recall:.2f}%")
    print(f"   F1 Score:        {f1:.2f}%")
    print(f"   Specificity:     {specificity:.2f}%")
    print(f"   Sensitivity:     {sensitivity:.2f}%")

    print("\n--- Latency Analysis ---")
    print(f"   Average Latency:     {avg_latency:>8.2f} ms")
    print(f"   Median Latency:      {median_lat:>8.2f} ms")
    print(f"   95th Percentile:     {p95_lat:>8.2f} ms")
    print(f"   Max Latency:         {max_lat:>8.2f} ms")

    print("="*55)
    print("End of Research Evaluation.")

if __name__ == "__main__":
    run_evaluation()