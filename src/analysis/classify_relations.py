"""Phase 7.3: classify the relationship between a review and the OTHER
app(s) it mentions.

Categories:
  switching_away        -- reviewer states they're leaving THIS app for
                            the other one ("moving to gpay", "switch to X")
  switched_from_competitor -- reviewer states they came FROM the other
                            app TO this one ("came from paytm", "better
                            than my old app X")
  comparison_only        -- evaluative comparison without a stated switch
                            ("X is better", "unlike gpay which...")
  none                   -- incidental mention, no clear relation

Rule-based (regex on explicit switching/comparison language), not an
ML classifier -- deliberate choice given the roadmap's "use an LLM or
hand-label the candidates" framing and this session's established
pattern (Phase 4) of substituting validated rule/keyword-based methods
when full ML/API-based labeling isn't proportionate to task size.
Validated against a hand-checked sample in validate_relations.py.
"""
import re

import pandas as pd

AWAY_PATTERNS = [
    r"switch(?:ing|ed)?\s+to\s+(?:the\s+)?{app}",   # "-ed" catches past-tense "switched to X"
    r"mov(?:e|ing|ed)\s+to\s+(?:the\s+)?{app}",
    r"shift(?:ing|ed)?\s+to\s+(?:the\s+)?{app}",
    r"migrat(?:e|ing|ed)\s+to\s+(?:the\s+)?{app}",
    r"go(?:ing)?\s+(?:back\s+)?to\s+(?:use\s+)?(?:the\s+)?{app}",
    r"going\s+for\s+{app}",
    r"(?:will|gonna|i\s*'?ll)\s+use\s+{app}",
    r"better\s+(?:to\s+)?use\s+{app}",
    r"use\s+{app}\s+instead",
    r"instead\s+use\s+{app}",                        # reverse word order
    r"uninstall(?:ing|ed)?.{{0,40}}(?:use|try)\s+{app}",
    r"deleting.{{0,20}}using\s+{app}",
    r"(?:now|so|then)?\s*(?:i\s*'?m\s+|i\s+am\s+)using\s+{app}",   # "now using X" / "I'm using X"
    r"stick(?:ing)?\s+with\s+{app}",
    r"mostly\s+use\s+{app}",
]

FROM_PATTERNS = [
    r"came\s+from\s+{app}",
    r"switched\s+from\s+{app}",
    r"mov(?:ed|ing)\s+from\s+{app}",
    r"shifted\s+from\s+{app}",
    r"used\s+to\s+use\s+{app}",
    r"previously\s+use[ds]?\s+{app}",
    r"earlier\s+(?:i\s+)?use[ds]?\s+{app}",
    r"left\s+{app}",
]

COMPARISON_PATTERNS = [
    # allow 0-2 filler words between the app name and "is" (e.g. "bhim
    # app is better", not just "bhim is better"), and between "is" and
    # the comparative word (e.g. "is actually faster")
    r"{app}(?:\s+\w+){{0,2}}\s+is\s+(?:\w+\s+){{0,2}}(?:better|worse|easier|faster|slower|best|hero)",
    r"(?:better|worse|easier|faster|slower|more\s+useful|more\s+better)\s+than\s+{app}",
    r"unlike\s+{app}",
    r"compared\s+to\s+{app}",
    r"compare\s+(?:with|to)\s+{app}",
    r"{app}\s+(?:gives?|has|offers?|provides?)",  # feature comparisons naming the other app
    r"like\s+{app}",
    r"same\s+as\s+{app}",
    r"not\s+like\s+{app}",
    r"rather\s+than\s+{app}",
    # A handful of common Hinglish comparative constructions actually
    # observed in the validation sample -- NOT full Hindi coverage
    # (that would need real NLP, out of scope here); documented as a
    # known limitation regardless.
    r"(?:isse|is\s+se)\s+(?:acha|accha|behtar|best)\s+{app}",   # "isse acha/behtar X" = "X is better than this"
    r"{app}\s+(?:hero|best|acha|accha|behtar)\s+hai",           # "X best/acha hai"
    r"{app}\s+se\s+(?:acha|accha|behtar)",                       # "X se acha" = "better than X"
]


def build_patterns(app_variants):
    app_group = "(?:" + "|".join(re.escape(v) for v in app_variants) + ")"
    return {
        "switching_away": [re.compile(p.format(app=app_group), re.IGNORECASE) for p in AWAY_PATTERNS],
        "switched_from_competitor": [re.compile(p.format(app=app_group), re.IGNORECASE) for p in FROM_PATTERNS],
        "comparison_only": [re.compile(p.format(app=app_group), re.IGNORECASE) for p in COMPARISON_PATTERNS],
    }


def classify_one(text, app_variants):
    patterns = build_patterns(app_variants)
    for relation in ["switching_away", "switched_from_competitor", "comparison_only"]:
        for pat in patterns[relation]:
            if pat.search(text):
                return relation
    return "none"


def main():
    import yaml
    with open(r"D:\projects\non-tech\config\aliases.yaml") as f:
        aliases = yaml.safe_load(f)

    candidates = pd.read_csv(r"D:\projects\non-tech\data\interim\competitor_mention_candidates.csv")
    candidates["other_mentions"] = candidates["other_mentions_str"].str.split(";")

    rows = []
    for _, row in candidates.iterrows():
        for other_app in row["other_mentions"]:
            relation = classify_one(row["review_text"], aliases[other_app])
            rows.append({
                "review_id": row["review_id"], "app_key": row["app_key"], "rating": row["rating"],
                "review_date": row["review_date"], "other_app": other_app, "relation": relation,
            })

    result = pd.DataFrame(rows)
    print(f"Classified {len(result):,} (review, other_app) pairs from {len(candidates):,} candidate reviews")
    print("\nRelation distribution:")
    print(result["relation"].value_counts())
    print("\nRelation distribution by other_app:")
    print(pd.crosstab(result["other_app"], result["relation"]))

    result.to_csv(r"D:\projects\non-tech\data\interim\relation_classified.csv", index=False, encoding="utf-8")
    print("\nSaved to data/interim/relation_classified.csv")


if __name__ == "__main__":
    main()
