// Labels and artifact kinds people actually attach to interpretability
// artifacts. **Suggestions, not a permitted set.**
//
// This file is the reason the picker uses a text input with a datalist rather
// than a dropdown. `CLAUDE.md` says a closed enumeration "declares which ways of
// doing the thing are legitimate" and instructs: document common values, enforce
// none. A `<select>` of a hundred concepts grouped into nine categories is a
// taxonomy and would be the closed-enum failure arriving through a control. A
// datalist behind a free-text field is the same information with none of the
// authority: the field takes anything and these merely autocomplete.
//
// **Provenance, stated because it matters.** This is a compiled list, not a
// cited one. Some entries trace to specific work that anybody in the field will
// recognise, Golden Gate Bridge to Anthropic's feature steering, Othello board
// state to Li et al., refusal to Arditi et al., sycophancy to the CAA line, and
// most do not trace to anything in particular. Nothing here is a claim that a
// given concept has been successfully isolated by anyone. It is a list of words
// people have used.
//
// The grouping is for reading, and is flattened before it reaches the page,
// because a datalist has no notion of groups and inventing one in the markup
// would reintroduce the taxonomy through the back door.

export const OBSERVED_LABELS: Record<string, string[]> = {
  "Safety and behavioural dispositions": [
    "refusal", "compliance", "harmfulness", "jailbreak-susceptibility",
    "sycophancy", "deception", "lying", "sandbagging", "reward-hacking",
    "power-seeking", "self-preservation", "shutdown-resistance",
    "alignment-faking", "sabotage", "withholding", "manipulation",
    "whistleblowing",
  ],
  "Epistemic states": [
    "truthfulness", "known-vs-unknown", "uncertainty", "confidence",
    "hallucination", "entity-recognition", "factual-recall", "belief-vs-assertion",
    "chain-of-thought-faithfulness",
  ],
  "Character and persona": [
    "kindness", "warmth", "helpfulness", "honesty", "humility", "arrogance",
    "evil", "sarcasm", "humor", "formality", "verbosity", "enthusiasm",
    "bluntness", "pedantry", "assistant-persona", "sentience-claiming",
    "pro-human",
  ],
  "Affect": [
    "valence", "arousal", "distress", "anxiety", "anger", "sadness", "joy",
    "curiosity", "boredom", "frustration", "inner-conflict",
  ],
  "Self-model and situational awareness": [
    "i-am-an-ai", "evaluation-awareness", "deployment-vs-training",
    "self-vs-other", "introspective-access", "tool-use-awareness",
    "observed-awareness",
  ],
  "Social and demographic": [
    "gender", "race", "age", "nationality", "religion", "political-leaning",
    "socioeconomic-class", "sentiment-toward-group",
  ],
  "Concrete concepts": [
    "golden-gate-bridge", "brooklyn-bridge", "transit-infrastructure",
    "dna-sequences", "python-code", "code-errors", "legal-language",
    "immigration", "tourist-attractions", "named-people", "months", "currencies",
  ],
  "World model and structure": [
    "board-state", "spatial-coordinates", "latitude-longitude", "time-and-date",
    "physical-scale", "causal-direction", "syntax-trees", "coreference",
  ],
  "Task and format control": [
    "language-selection", "output-format", "instruction-following",
    "register-transfer", "task-vector", "function-vector",
  ],
};

// Artifact kinds. `kind` is an open string in the schema and these are the
// spellings in circulation, not the ones the schema accepts.
export const OBSERVED_KINDS: string[] = [
  "direction", "linear-probe", "difference-of-means", "caa-vector",
  "persona-vector", "steering-vector", "sae-latent", "transcoder-feature",
  "circuit", "attention-head-role", "task-vector", "function-vector",
  "causal-mask", "lora", "reft",
];

export const ALL_LABELS: string[] = Object.values(OBSERVED_LABELS).flat();
