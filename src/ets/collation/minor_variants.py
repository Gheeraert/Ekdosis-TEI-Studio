from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

try:  # pragma: no cover - dependency error is clearer at import time
    from rapidfuzz.distance import DamerauLevenshtein, Levenshtein
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "RapidFuzz is required for minor-variant classification. "
        "Install it with: pip install rapidfuzz"
    ) from exc


SPACE_MARKERS = {"~", "\u00a0", "\u202f"}
HYPHENS = {"-", "‐", "‑", "‒", "–", "—"}
APOSTROPHES = {"'", "’", "‘", "ʼ", "`", "´"}

HIDE_SAFE_CLASSES = {
    "minor_punctuation",
    "minor_spacing",
    "minor_case",
    "minor_graphic_safe",
}

VARIANT_ANA_CATEGORIES: dict[str, str] = {
    "accent": "Variation d'accentuation.",
    "accent_only": "Variation limitee a l'accentuation.",
    "apostrophe": "Variation d'apostrophe.",
    "case_only": "Variation limitee aux majuscules et minuscules.",
    "damerau_metathesis": "Metathese graphique probable.",
    "double_consonant": "Variation de consonne double.",
    "final_t_before_s": "Variation de t etymologique avant s final.",
    "final_zx_s": "Variation graphique finale z/x/s.",
    "historic_graphic_key_identity": "Identite apres normalisation graphique historique.",
    "historic_spelling": "Variation de graphie historique.",
    "i_j": "Variation graphique entre i et j.",
    "levenshtein_alert": "Proximite graphique probable.",
    "ligature_or_long_s": "Variation de ligature ou de s long.",
    "literal_identity": "Identite litterale.",
    "punctuation_only": "Variation limitee a la ponctuation.",
    "punctuation_removed_for_graphic_key": "Ponctuation neutralisee pour la comparaison graphique.",
    "spacing_or_hyphen": "Variation d'espace ou de trait d'union.",
    "spacing_or_hyphen_only": "Variation limitee aux espaces ou aux traits d'union.",
    "u_v": "Variation graphique entre u et v.",
    "whole_line_variant": "Variante de vers entier.",
    "y_i": "Variation graphique entre y et i.",
}

INSPECT_CLASSES = {
    "minor_graphic_probable",
    "minor_metathesis_probable",
    "minor_mixed",
}


@dataclass(frozen=True)
class VariantClassification:
    """Conservative classification for a token-level apparatus.

    ``visibility_policy`` is the important downstream decision:
    - ``hide_safe``: the apparatus may be hidden in a readable PDF;
    - ``inspect``: the apparatus is probably minor but should remain visible;
    - ``visible``: the apparatus is substantive or mixed and must remain visible.
    """

    candidate_class: str
    visibility_policy: str
    rule_code: str
    reason: str

    @property
    def is_minor(self) -> bool:
        return self.visibility_policy in {"hide_safe", "inspect"}

    @property
    def subtype(self) -> str:
        return subtype_for_candidate_class(self.candidate_class)


SUBTYPE_BY_CLASS = {
    "minor_punctuation": "punctuation",
    "minor_spacing": "spacing",
    "minor_case": "case",
    "minor_graphic_safe": "graphic",
    "minor_graphic_probable": "graphic-probable",
    "minor_metathesis_probable": "metathesis-probable",
    "minor_mixed": "mixed",
    "mixed_minor_and_substantive": "mixed-substantive",
    "substantive": "substantive",
    "whole_line_variant": "whole-line",
    "identical": "identical",
}


def subtype_for_candidate_class(candidate_class: str) -> str:
    return SUBTYPE_BY_CLASS.get(candidate_class, candidate_class.replace("_", "-"))


def ana_tokens_from_rule_code(rule_code: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw_token in rule_code.replace("+", " ").split():
        token = raw_token.strip()
        if not token:
            continue
        tokens.append(token[1:] if token.startswith("#") else token)
    return tuple(dict.fromkeys(tokens))


def format_ana_tokens(tokens: Sequence[str]) -> str:
    normalized: list[str] = []
    for raw_token in tokens:
        token = raw_token.strip()
        if not token:
            continue
        normalized.append(token if token.startswith("#") else f"#{token}")
    return " ".join(dict.fromkeys(normalized))


def format_ana_rule_code(rule_code: str) -> str:
    return format_ana_tokens(ana_tokens_from_rule_code(rule_code))


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for char in APOSTROPHES:
        text = text.replace(char, "'")
    for char in HYPHENS:
        text = text.replace(char, "-")
    return text


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def is_punctuation(char: str) -> bool:
    return unicodedata.category(char).startswith("P")


def is_space_like(char: str) -> bool:
    return char.isspace() or unicodedata.category(char).startswith("Z") or char in SPACE_MARKERS


def letters_and_numbers(text: str) -> str:
    text = normalize_unicode(text).lower()
    return "".join(ch for ch in text if unicodedata.category(ch)[0] in {"L", "N"})


def letters_and_numbers_unaccented(text: str) -> str:
    return strip_accents(letters_and_numbers(text))


def remove_spaces_and_hyphens(text: str) -> str:
    text = normalize_unicode(text).lower()
    return "".join(ch for ch in text if not is_space_like(ch) and ch not in HYPHENS)


def punctuation_signature(text: str) -> str:
    text = normalize_unicode(text)
    return "".join(ch for ch in text if is_punctuation(ch) and ch not in HYPHENS)


def has_punctuation_difference(left: str, right: str) -> bool:
    return punctuation_signature(left) != punctuation_signature(right)


def remove_punctuation(text: str) -> str:
    text = normalize_unicode(text)
    chars: list[str] = []
    for index, ch in enumerate(text):
        previous_char = text[index - 1] if index > 0 else ""
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if is_punctuation(ch) and ch not in HYPHENS:
            continue
        if (is_space_like(ch) or ch in SPACE_MARKERS) and (
            (previous_char and is_punctuation(previous_char) and previous_char not in HYPHENS)
            or (next_char and is_punctuation(next_char) and next_char not in HYPHENS)
        ):
            continue
        chars.append(ch)
    return "".join(chars)


def _minor_feature_key(text: str, features: frozenset[str]) -> str:
    current = normalize_unicode(text)
    if "punctuation_only" in features:
        current = remove_punctuation(current)
    if "spacing_or_hyphen_only" in features:
        current = "".join(ch for ch in current if not is_space_like(ch) and ch not in HYPHENS)
    if "accent" in features:
        current = strip_accents(current)
    if "case_only" in features:
        current = current.lower()
    return current


_SIMPLE_MINOR_FEATURES = (
    "case_only",
    "spacing_or_hyphen_only",
    "punctuation_only",
    "accent",
)


def classify_simple_minor_features(left: str, right: str) -> VariantClassification | None:
    for size in range(1, len(_SIMPLE_MINOR_FEATURES) + 1):
        for feature_group in combinations(_SIMPLE_MINOR_FEATURES, size):
            features = frozenset(feature_group)
            if _minor_feature_key(left, features) != _minor_feature_key(right, features):
                continue
            if size == 1:
                feature = feature_group[0]
                if feature == "case_only":
                    return VariantClassification("minor_case", "hide_safe", feature, feature)
                if feature == "spacing_or_hyphen_only":
                    return VariantClassification("minor_spacing", "hide_safe", feature, feature)
                if feature == "punctuation_only" and has_punctuation_difference(left, right):
                    return VariantClassification("minor_punctuation", "hide_safe", feature, feature)
                if feature == "accent":
                    return VariantClassification("minor_graphic_safe", "hide_safe", "accent", "accent_only")
                continue
            rule_code = "+".join(feature_group)
            return VariantClassification("minor_mixed", "hide_safe", rule_code, rule_code)
    return None


def apply_historic_graphic_rules(token: str) -> tuple[str, tuple[str, ...]]:
    """Return a comparison key plus the named rules used to create it.

    The key is used only for classification. It never rewrites the edited text.
    Rules are deliberately narrow and generic for early-modern French.
    """
    rules: list[str] = []
    current = normalize_unicode(token).lower()

    expanded = current.replace("œ", "oe").replace("æ", "ae").replace("ſ", "s")
    if expanded != current:
        rules.append("ligature_or_long_s")
        current = expanded

    unaccented = strip_accents(current)
    if unaccented != current:
        rules.append("accent")
        current = unaccented

    chars: list[str] = []
    removed_spacing = False
    removed_apostrophe = False
    removed_punctuation = False
    for ch in current:
        if is_space_like(ch) or ch in HYPHENS:
            removed_spacing = True
            continue
        if ch in APOSTROPHES:
            removed_apostrophe = True
            continue
        if is_punctuation(ch):
            removed_punctuation = True
            continue
        chars.append(ch)
    current = "".join(chars)
    if removed_spacing:
        rules.append("spacing_or_hyphen")
    if removed_apostrophe:
        rules.append("apostrophe")
    if removed_punctuation:
        rules.append("punctuation_removed_for_graphic_key")

    replaced = current.replace("j", "i")
    if replaced != current:
        rules.append("i_j")
        current = replaced

    replaced = current.replace("v", "u")
    if replaced != current:
        rules.append("u_v")
        current = replaced

    replaced = current.replace("y", "i")
    if replaced != current:
        rules.append("y_i")
        current = replaced

    replaced = current
    replaced = replaced.replace("soust", "sout")
    replaced = replaced.replace("mesmes", "memes")
    replaced = replaced.replace("mesme", "meme")
    replaced = replaced.replace("vostres", "votres").replace("vostre", "votre")
    replaced = replaced.replace("uostres", "uotres").replace("uostre", "uotre")
    replaced = replaced.replace("nostres", "notres").replace("nostre", "notre")
    replaced = replaced.replace("plutost", "plutot")
    replaced = replaced.replace("prest", "pret")
    replaced = replaced.replace("maistr", "maitr")
    replaced = replaced.replace("peutestre", "peutetre")
    replaced = replaced.replace("estre", "etre")
    replaced = replaced.replace("este", "ete")
    replaced = replaced.replace("eust", "eut")
    replaced = replaced.replace("estat", "etat")
    replaced = replaced.replace("oistr", "oitr")
    replaced = replaced.replace("connoi", "connai")
    replaced = replaced.replace("connoitr", "connaitr")
    replaced = replaced.replace("traisn", "train")
    replaced = replaced.replace("experiance", "experience")
    replaced = replaced.replace("audiance", "audience")
    replaced = replaced.replace("tousiours", "toujours").replace("tousjours", "toujours")
    replaced = replaced.replace("gaigner", "gagner")
    replaced = replaced.replace("dounant", "donnant")
    replaced = replaced.replace("esteindre", "eteindre")
    replaced = replaced.replace("entraisn", "entrain")
    # V8 ultra-prudente : résidus graphiques validés sur Britannicus.
    replaced = replaced.replace("bientost", "bientot")
    replaced = replaced.replace("tems", "temps")
    replaced = replaced.replace("doi", "dois")
    replaced = replaced.replace("sceu", "su")
    replaced = replaced.replace("scau", "sau")
    replaced = replaced.replace("piez", "pieds")
    replaced = replaced.replace("condanne", "condamne")
    replaced = replaced.replace("espoux", "epoux")
    replaced = replaced.replace("auouerez", "auoures")
    replaced = replaced.replace("auoueres", "auoures")
    replaced = replaced.replace("auourez", "auoures")
    replaced = replaced.replace("asseure", "assure")
    replaced = replaced.replace("estois", "etois")
    replaced = replaced.replace("fai", "fais")
    replaced = replaced.replace("sçache", "sache")
    replaced = replaced.replace("ponr", "pour")
    if replaced != current:
        rules.append("historic_spelling")
        current = replaced

    # Common endings: sauvéz/sauvés, peus/peux, including forms followed by a
    # normalized clitic after hyphen removal (attendesuous / attendezvous).
    replaced = re.sub(r"[zx]$", "s", current)
    replaced = re.sub(
        r"[zx](?=(ie|tu|il|elle|on|nous|uous|ils|elles|moi|toi|lui|leur|en|i)$)",
        "s",
        replaced,
    )
    if replaced != current:
        rules.append("final_zx_s")
        current = replaced

    # Optional etymological t before final s: rempars/remparts, enfans/enfants.
    replaced = re.sub(r"t(?=s$)", "", current) if len(current) >= 7 else current
    if replaced != current:
        rules.append("final_t_before_s")
        current = replaced

    replaced = re.sub(r"([bcdfghjklmnpqrstvwxz])\1+", r"\1", current)
    if replaced != current:
        rules.append("double_consonant")
        current = replaced

    return current, tuple(sorted(set(rules)))


def historic_graphic_normalize(token: str) -> str:
    return apply_historic_graphic_rules(token)[0]


def protected_short_token(left: str, right: str, min_len: int) -> bool:
    return min(len(letters_and_numbers(left)), len(letters_and_numbers(right))) <= min_len


def classify_pair(
    left: str,
    right: str,
    *,
    min_length_for_distance: int = 4,
    graphic_similarity_threshold: float = 0.90,
    metathesis_min_length: int = 6,
    max_distance: int = 2,
) -> VariantClassification:
    left_norm = normalize_unicode(left.strip())
    right_norm = normalize_unicode(right.strip())

    if left_norm == right_norm:
        return VariantClassification("identical", "hide_safe", "literal_identity", "literal_identity")

    simple_classification = classify_simple_minor_features(left_norm, right_norm)
    if simple_classification is not None:
        return simple_classification

    left_graphic, left_rules = apply_historic_graphic_rules(left_norm)
    right_graphic, right_rules = apply_historic_graphic_rules(right_norm)
    if left_graphic == right_graphic and left_graphic:
        rules = sorted(set(left_rules) | set(right_rules))
        rule_code = "+".join(rules) if rules else "historic_graphic_key_identity"
        return VariantClassification(
            "minor_graphic_safe", "hide_safe", rule_code, "historic_graphic_key_identity"
        )

    if protected_short_token(left_norm, right_norm, min_length_for_distance):
        return VariantClassification("substantive", "visible", "short_token_protected", "short_token_protected")

    graphic_lev_d = Levenshtein.distance(left_graphic, right_graphic)
    graphic_dam_d = DamerauLevenshtein.distance(left_graphic, right_graphic)
    graphic_sim = max(
        Levenshtein.normalized_similarity(left_graphic, right_graphic),
        DamerauLevenshtein.normalized_similarity(left_graphic, right_graphic),
    )

    if (
        min(len(left_graphic), len(right_graphic)) >= metathesis_min_length
        and graphic_dam_d == 1
        and graphic_lev_d == 2
        and graphic_sim >= graphic_similarity_threshold
    ):
        return VariantClassification(
            "minor_metathesis_probable", "inspect", "damerau_metathesis", f"possible_metathesis:{graphic_sim:.3f}"
        )

    if graphic_sim >= graphic_similarity_threshold and min(graphic_lev_d, graphic_dam_d) <= max_distance:
        return VariantClassification(
            "minor_graphic_probable", "inspect", "levenshtein_alert", f"high_graphic_similarity:{graphic_sim:.3f}"
        )

    return VariantClassification("substantive", "visible", "substantive_default", "low_similarity_or_real_rewriting")


def aggregate_pair_classifications(classifications: Sequence[VariantClassification]) -> VariantClassification:
    classes = {item.candidate_class for item in classifications if item.candidate_class != "identical"}
    reasons = sorted({item.reason for item in classifications if item.reason != "literal_identity"})
    rules = sorted({item.rule_code for item in classifications if item.rule_code != "literal_identity"})

    if not classes:
        return VariantClassification("identical", "hide_safe", "literal_identity", "literal_identity")

    reason = ";".join(reasons) if reasons else "literal_identity"
    rule_code = "+".join(rules) if rules else "literal_identity"

    non_identical = [item for item in classifications if item.candidate_class != "identical"]
    if non_identical and all(item.visibility_policy == "hide_safe" for item in non_identical):
        if len(classes) == 1:
            candidate_class = next(iter(classes))
        else:
            candidate_class = "minor_mixed"
        return VariantClassification(candidate_class, "hide_safe", rule_code, reason)

    if classes <= (HIDE_SAFE_CLASSES | INSPECT_CLASSES):
        return VariantClassification("minor_mixed", "inspect", rule_code, reason)

    if "substantive" in classes and (classes & (HIDE_SAFE_CLASSES | INSPECT_CLASSES)):
        return VariantClassification("mixed_minor_and_substantive", "visible", rule_code, reason)

    return VariantClassification("substantive", "visible", rule_code, reason)


def classify_apparatus(lemma: str, readings: Sequence[str]) -> VariantClassification:
    """Classify an apparatus from the lemma and variant reading texts."""
    unique = list(dict.fromkeys([lemma, *readings]))
    if len(unique) <= 1:
        return VariantClassification("identical", "hide_safe", "literal_identity", "literal_identity")
    pairwise = [
        classify_pair(left, right)
        for index, left in enumerate(unique)
        for right in unique[index + 1 :]
    ]
    return aggregate_pair_classifications(pairwise)


def whole_line_classification() -> VariantClassification:
    return VariantClassification(
        candidate_class="whole_line_variant",
        visibility_policy="visible",
        rule_code="whole_line_variant",
        reason="whole_line_variant",
    )
