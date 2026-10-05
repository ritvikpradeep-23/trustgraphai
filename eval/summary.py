"""Write reports/<date>/summary.md from a finished run."""
import json


def _pct(x) -> str:
    return "n/a" if x is None or x != x else f"{x:.1%}"


def _ci(r) -> str:
    return f"{_pct(r['value'])} [{_pct(r['lo'])}, {_pct(r['hi'])}]"


def write_summary(run):
    res, m = run.results, run.manifest
    L = ["# TrustGraph evaluation summary", "",
         "> **All numbers come from synthetic, AI-written messages.** They show how the engine behaves on "
         "this generated data, not its real-world accuracy. Fake placeholders only; no real people, numbers or links.", "",
         f"- Frozen test set: `{m['test_file']}`, sha256 `{m['test_sha256'][:16]}…` (verified at start of run), "
         f"generator seed {m['generator_seed']}, {m['removed_by_leakage_filter']} message(s) removed by the leakage filter (>0.9 similarity).",
         f"- Test set: {m['counts']['test'].get('scam', 0)} scams across 29 types (13 the engine has reference examples for, "
         f"16 it has never seen) and {m['counts']['test'].get('legit', 0)} honest messages across 13 types.",
         "- Thresholds are calibrated on **dev** honest messages only (Caution flags ~10%, High ~1%) and written to "
         "`thresholds.json` here, never to `models/`. Nothing was tuned on the test set.", ""]

    if "metrics" in res:
        h = res["metrics"]["headline"]
        L += ["## Headline (text only, as a text-only client would send)", "",
              "| | Caution or above | High |", "|---|---|---|",
              f"| Scams caught, all types | {_ci(h['recall_caution'])} | {_ci(h['recall_high'])} |",
              f"| Scams caught, types with reference examples | {_ci(h['recall_caution_seen'])} | {_ci(h['recall_high_seen'])} |",
              f"| Scams caught, never-seen types | {_ci(h['recall_caution_unseen'])} | {_ci(h['recall_high_unseen'])} |",
              f"| Honest messages flagged (false alarms) | {_ci(h['fpr_caution'])} | {_ci(h['fpr_high'])} |",
              f"| Precision | {_pct(h['precision_caution']['value'])} | {_pct(h['precision_high']['value'])} |", "",
              f"ROC-AUC {h['roc_auc']:.3f} [{h['roc_auc_ci'][0]:.3f}, {h['roc_auc_ci'][1]:.3f}], "
              f"PR-AUC {h['pr_auc']:.3f} [{h['pr_auc_ci'][0]:.3f}, {h['pr_auc_ci'][1]:.3f}]. "
              f"Precision depends on this set's {h['n_scam']}:{h['n_legit']} scam-to-honest ratio; real traffic has far fewer scams.", "",
              "### Scams caught per type (Caution or above, 95% CI)", "",
              "| Type | Seen? | n | Caution | High |", "|---|---|---|---|---|"]
        for t in sorted(res["metrics"]["per_category"], key=lambda t: (t["novelty"], -t["caution"])):
            L.append(f"| {t['category']} | {t['novelty']} | {t['n']} | {_pct(t['caution'])} "
                     f"[{_pct(t['caution_lo'])}, {_pct(t['caution_hi'])}] | {_pct(t['high'])} |")
        L += ["", "### By language and evasion trick (scams caught at Caution)", ""]
        for f in ("language", "evasion_type"):
            L.append(", ".join(f"{t[f]} {_pct(t['caution'])} (n={t['n']})" for t in res["metrics"]["groups"][f]) + ".")
            L.append("")

    if "loco" in res:
        s = res["loco"]["summary"]
        L += ["## Unseen scam types: leave-one-category-out", "",
              f"For each of the 13 types with reference examples, the examples were removed, thresholds recalibrated on dev, "
              f"and that type measured. Mean caught: **{_pct(s['seen_full_corpus_mean'])} with its examples → "
              f"{_pct(s['seen_left_out_mean'])} without** (wording match alone: {_pct(s['seen_left_out_wording_only_mean'])}). "
              f"The 16 never-seen types average **{_pct(s['unseen_mean'])}**. The red-flag rules can't be left out this way and "
              "were written by someone who knew many scam types, so treat the full-engine number as an upper bound.", "",
              "| Type | With examples | Left out | Left out, wording only |", "|---|---|---|---|"]
        for t in res["loco"]["table"]:
            if t["in_reference_corpus"]:
                L.append(f"| {t['category']} | {_pct(t['recall_full_corpus'])} | {_pct(t['loco_fused'])} | {_pct(t['loco_wording'])} |")
        L.append("")

    if "ablation" in res:
        L += ["## Which signal does the work (each at its own matched ~10% false-alarm rate)", "",
              "| Score | Caught (Caution) | Never-seen types | False alarms (test) | ROC-AUC |", "|---|---|---|---|---|"]
        for t in res["ablation"]:
            L.append(f"| {t['what']} | {_pct(t['recall_caution'])} | {_pct(t['recall_caution_unseen'])} | "
                     f"{_pct(t['test_false_alarms_caution'])} | {t['roc_auc']:.3f} |")
        L += ["", "### With call details", "",
              "| Setting | Caught (Caution) | False alarms | ROC-AUC |", "|---|---|---|---|"]
        names = {"text_only": "text only", "metadata_same": "text + call details, same for scam and honest",
                 "metadata_skewed": "text + call details where scams look unusual (**assumption**)"}
        for t in res["metadata_settings"]:
            if t["score"] == "fused":
                L.append(f"| {names[t['setting']]} | {_pct(t['recall_caution'])} | {_pct(t['test_false_alarms_caution'])} | {t['roc_auc']:.3f} |")
        L += ["", "Call details that carry no information make honest scores noisier and lower detection; they only help if "
              "scams really do arrive at odd hours, in bursts, from new senders.", ""]

    if "errors" in res:
        e = res["errors"]
        L += ["## Errors on the frozen test set (text only)", "",
              f"{e['n_false_negatives']} scams missed, {e['n_false_positives']} honest messages flagged. "
              "Full lists with the engine's explanations: `false_negatives_worst.csv`, `false_positives_worst.csv`, `error_groups.csv`.", "",
              "Highest error rates by group:", ""]
        for kind in ("missed scam", "false alarm"):
            top = sorted([g for g in e["groups"] if g["error"] == kind and g["of"] >= 20], key=lambda g: -g["rate"])[:6]
            L.append(f"- **{kind}**: " + "; ".join(f"{g['field']}={g['value']} {g['errors']}/{g['of']} ({g['rate']:.0%})" for g in top))
        L += ["", "Worst misses:", ""]
        for r in e["worst_false_negatives"][:5]:
            L.append(f"- [{r['category']}, {r['language']}] \"{r['text'][:110]}\" → {r['engine_explanation'][:90]}")
        L += ["", "Worst false alarms:", ""]
        for r in e["worst_false_positives"][:5]:
            L.append(f"- [{r['category']}, {r['language']}] \"{r['text'][:110]}\" → {r['engine_explanation'][:90]}")
        L.append("")

    if "report_once" in res:
        s = res["report_once"]["summary"]
        L += ["## Report-once experiment", "",
              f"{s['reported']} scams the engine missed in fresh batch A (seed {s['seed_a']}) were added to a copy of its reference "
              f"examples, thresholds were recalibrated on dev, and a different fresh batch B (seed {s['seed_b']}, "
              f"{s['batch_b_scams']} scams, excluding the reported messages' families and near-copies) was measured.", "",
              "| Variant | Caught before | Caught after | Dev false alarms after |", "|---|---|---|---|"]
        for name, label in (("scam_reports_only", "scam reports only"),
                            ("plus_legit", f"scam reports + {s['legit_added_in_plus_legit']} honest examples")):
            v = s["variants"][name]
            L.append(f"| {label} | {_pct(v['recall_before']['value'])} | {_ci(v['recall_after'])} | {_pct(v['dev_false_alarms_after'])} |")
        L += ["", "Scam reports alone backfire: many were Hinglish/Manglish, the honest reference examples are English, so honest "
              "messages in those languages start resembling the reports and the threshold must jump. Adding a few honest examples "
              "in the same languages turns it into a clear gain.", ""]

    if "sms" in res:
        s = res["sms"]
        L += ["## Real-world false-alarm check", "",
              f"{s['legit']['n']} genuine non-scam texts from the public UCI SMS Spam Collection (UK, 2000s): "
              f"**{_ci(s['legit']['caution'])} flagged at Caution**, {_ci(s['legit']['high'])} at High. "
              f"Its spam is mostly marketing, not scams; {_pct(s['spam']['caution']['value'])} of it is flagged.", ""]

    if "fresh_batch" in res:
        fb = res["fresh_batch"]
        L += [f"## Fresh batch (seed {fb['seed']})", "",
              f"Recall at Caution {_ci(fb['metrics']['recall_caution'])}, false alarms {_ci(fb['metrics']['fpr_caution'])} "
              f"after removing {fb['dropped_near_copies']} near-copies. New fills of the same hand-written seeds: a stability check, "
              "not a second untouched test set.", ""]

    L += ["## Limits", "",
          "- Synthetic data written by the same AI that built the engine: shared phrasing habits can flatter results.",
          "- Hinglish and Manglish were written by a non-native writer and may read unnaturally.",
          "- A few honest code messages contain an invoice-style number where the code should be (a generator slip); "
          "left in place because the test set is frozen.",
          "- Text only: continuity and precedent have nothing to work with unless account, number or history data are supplied.", "",
          "## Re-run", "", "```", "PYTHONPATH=src python -m eval.run                    # all sections",
          "PYTHONPATH=src python -m eval.run --batch-seed 7     # plus a fresh batch", "```", ""]
    (run.out / "summary.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {run.out / 'summary.md'}")
