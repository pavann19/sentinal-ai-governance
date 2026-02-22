# evaluation/adversarial_evaluate_v1.py
# Structured adversarial robustness evaluation for SentinAL v3.
# Usage: python adversarial_evaluate_v1.py

import sys
import os
import json
import time

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from governance.risk import assess_risk

# --- PATHS ---
DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "adversarial_dataset_v1.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")
RAW_OUTPUT = os.path.join(RESULTS_DIR, "adversarial_eval_v1.json")
SUMMARY_OUTPUT = os.path.join(RESULTS_DIR, "adversarial_summary_v1.txt")


def safe_div(numerator, denominator):
    """Division with zero-safety."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def load_dataset(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(dataset):
    """Run assess_risk() on every prompt and collect results."""
    results = []
    total = len(dataset)

    for i, entry in enumerate(dataset):
        prompt = entry["prompt"]
        start = time.time()
        risk, metadata = assess_risk(prompt)
        latency = time.time() - start

        results.append({
            "id": entry["id"],
            "category": entry["category"],
            "type": entry["type"],
            "expected_intent": entry["expected_intent"],
            "prompt": prompt,
            "predicted_risk": risk,
            "predicted_block": (risk == "HIGH"),
            "source": metadata.get("source", "unknown"),
            "judge_invoked": metadata.get("judge_invoked", False),
            "meta_intent_score": metadata.get("meta_intent_score"),
            "domain_score": metadata.get("domain_score"),
            "dynamic_threat_score": metadata.get("dynamic_threat_score"),
            "educational_context": metadata.get("educational_context", False),
            "semantic_score": metadata.get("semantic_score"),
            "latency_s": round(latency, 4)
        })

        # Progress indicator (ASCII only)
        if (i + 1) % 20 == 0 or (i + 1) == total:
            print(f"  [{i+1}/{total}] processed")

    return results


def compute_metrics(results):
    """Compute all evaluation metrics from raw results."""
    malicious = [r for r in results if r["type"] == "malicious"]
    benign_adv = [r for r in results if r["type"] == "benign_adversarial"]

    total = len(results)
    total_malicious = len(malicious)
    total_benign_adv = len(benign_adv)

    # --- CONFUSION MATRIX ---
    tp = sum(1 for r in malicious if r["predicted_risk"] == "HIGH")
    fn = sum(1 for r in malicious if r["predicted_risk"] != "HIGH")
    tn = sum(1 for r in benign_adv if r["predicted_risk"] != "HIGH")
    fp = sum(1 for r in benign_adv if r["predicted_risk"] == "HIGH")

    # --- OVERALL METRICS ---
    asr = safe_div(fn, total_malicious)
    fpr_benign_adv = safe_div(fp, total_benign_adv)

    # --- JUDGE INVOCATION ---
    judge_invoked_count = sum(1 for r in results if r["judge_invoked"])
    judge_invocation_rate = safe_div(judge_invoked_count, total)

    # --- LAYER CONTRIBUTION (over malicious only) ---
    meta_intent_detections = sum(1 for r in malicious if r["source"] == "semantic_meta_intent")
    domain_guardrail_detections = sum(1 for r in malicious if r["source"] == "domain_guardrail")
    vector_threat_detections = sum(1 for r in malicious if r["source"] == "vector_threat_critical")
    judge_detections = sum(1 for r in malicious if r["source"].startswith("semantic_judge"))
    safe_harbor_activations = sum(1 for r in malicious if r["source"] == "educational_safe_harbor")
    symbolic_detections = sum(1 for r in malicious if r["source"] == "symbolic_rule")
    judge_fail_closed = sum(1 for r in malicious if r["source"] == "judge_failure_fail_closed")

    layer_contribution = {
        "symbolic_rule_rate": safe_div(symbolic_detections, total_malicious),
        "meta_intent_detection_rate": safe_div(meta_intent_detections, total_malicious),
        "domain_guardrail_rate": safe_div(domain_guardrail_detections, total_malicious),
        "vector_threat_rate": safe_div(vector_threat_detections, total_malicious),
        "judge_detection_rate": safe_div(judge_detections, total_malicious),
        "judge_fail_closed_rate": safe_div(judge_fail_closed, total_malicious),
        "safe_harbor_activation_rate": safe_div(safe_harbor_activations, total_malicious),
    }

    # --- CATEGORY-WISE BREAKDOWN ---
    categories = sorted(set(r["category"] for r in results))
    category_metrics = {}
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_mal = [r for r in cat_results if r["type"] == "malicious"]
        cat_ben = [r for r in cat_results if r["type"] == "benign_adversarial"]

        cat_fn = sum(1 for r in cat_mal if r["predicted_risk"] != "HIGH")
        cat_fp = sum(1 for r in cat_ben if r["predicted_risk"] == "HIGH")

        category_metrics[cat] = {
            "total": len(cat_results),
            "malicious_count": len(cat_mal),
            "benign_count": len(cat_ben),
            "ASR": safe_div(cat_fn, len(cat_mal)),
            "FPR": safe_div(cat_fp, len(cat_ben)),
        }

    return {
        "total_prompts": total,
        "total_malicious": total_malicious,
        "total_benign_adversarial": total_benign_adv,
        "ASR_overall": asr,
        "FPR_benign_adversarial": fpr_benign_adv,
        "confusion_matrix": {"TP": tp, "FN": fn, "TN": tn, "FP": fp},
        "judge_invocation_rate": judge_invocation_rate,
        "layer_contribution": layer_contribution,
        "category_metrics": category_metrics,
    }


def write_raw_results(results, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Raw results saved to: {path}")


def write_summary(metrics, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    lines = []
    w = lines.append

    w("=" * 72)
    w("  SentinAL v3 -- ADVERSARIAL ROBUSTNESS EVALUATION REPORT")
    w("=" * 72)
    w("")
    w("--- DATASET SUMMARY ---")
    w(f"  Total Prompts:           {metrics['total_prompts']}")
    w(f"  Total Malicious:         {metrics['total_malicious']}")
    w(f"  Total Benign Adversarial:{metrics['total_benign_adversarial']}")
    w("")

    w("--- OVERALL METRICS ---")
    w(f"  Attack Success Rate (ASR):       {metrics['ASR_overall']:.4f}")
    w(f"  False Positive Rate (benign_adv): {metrics['FPR_benign_adversarial']:.4f}")
    w("")

    cm = metrics["confusion_matrix"]
    w("--- CONFUSION MATRIX ---")
    w(f"  True Positives  (malicious -> HIGH):     {cm['TP']}")
    w(f"  False Negatives (malicious -> not HIGH):  {cm['FN']}")
    w(f"  True Negatives  (benign_adv -> not HIGH): {cm['TN']}")
    w(f"  False Positives (benign_adv -> HIGH):     {cm['FP']}")
    w("")

    precision = safe_div(cm["TP"], cm["TP"] + cm["FP"])
    recall = safe_div(cm["TP"], cm["TP"] + cm["FN"])
    f1 = safe_div(2 * precision * recall, precision + recall)
    accuracy = safe_div(cm["TP"] + cm["TN"], cm["TP"] + cm["TN"] + cm["FP"] + cm["FN"])

    w("--- DERIVED CLASSIFICATION METRICS ---")
    w(f"  Accuracy:   {accuracy:.4f}")
    w(f"  Precision:  {precision:.4f}")
    w(f"  Recall:     {recall:.4f}")
    w(f"  F1 Score:   {f1:.4f}")
    w("")

    w("--- JUDGE INVOCATION ---")
    w(f"  Judge Invocation Rate: {metrics['judge_invocation_rate']:.4f}")
    w("")

    w("--- LAYER CONTRIBUTION (over malicious prompts) ---")
    lc = metrics["layer_contribution"]
    w(f"  Symbolic Rule Rate:            {lc['symbolic_rule_rate']:.4f}")
    w(f"  Meta-Intent Detection Rate:    {lc['meta_intent_detection_rate']:.4f}")
    w(f"  Domain Guardrail Rate:         {lc['domain_guardrail_rate']:.4f}")
    w(f"  Vector Threat Rate:            {lc['vector_threat_rate']:.4f}")
    w(f"  Judge Detection Rate:          {lc['judge_detection_rate']:.4f}")
    w(f"  Judge Fail-Closed Rate:        {lc['judge_fail_closed_rate']:.4f}")
    w(f"  Safe Harbor Activation Rate:   {lc['safe_harbor_activation_rate']:.4f}")
    w("")

    w("--- CATEGORY-WISE BREAKDOWN ---")
    w(f"  {'Category':<35} {'Total':>5} {'Mal':>5} {'Ben':>5} {'ASR':>8} {'FPR':>8}")
    w("  " + "-" * 68)
    for cat, m in metrics["category_metrics"].items():
        w(f"  {cat:<35} {m['total']:>5} {m['malicious_count']:>5} {m['benign_count']:>5} {m['ASR']:>8.4f} {m['FPR']:>8.4f}")
    w("")

    w("=" * 72)
    w("  END OF REPORT")
    w("=" * 72)

    text = "\n".join(lines)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(text)
    print(f"\nSummary saved to: {path}")


# --- MAIN ---
if __name__ == "__main__":
    print("=" * 72)
    print("  SentinAL v3 -- Adversarial Evaluation Runner")
    print("=" * 72)

    # 1. Load dataset
    dataset_path = os.path.abspath(DATASET_PATH)
    print(f"\nLoading dataset: {dataset_path}")
    dataset = load_dataset(dataset_path)
    print(f"Loaded {len(dataset)} prompts.\n")

    # 2. Run evaluation
    print("Running evaluation...")
    results = run_evaluation(dataset)
    print(f"\nEvaluation complete. {len(results)} prompts processed.\n")

    # 3. Save raw results
    write_raw_results(results, os.path.abspath(RAW_OUTPUT))

    # 4. Compute metrics
    metrics = compute_metrics(results)

    # 5. Write summary report
    print("")
    write_summary(metrics, os.path.abspath(SUMMARY_OUTPUT))
