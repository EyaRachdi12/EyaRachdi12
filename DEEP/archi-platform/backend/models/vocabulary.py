"""
Vocabulary for the Caption model.
Built from architectural floor plan descriptions.
"""

from typing import List, Dict

# ── Architectural vocabulary ──────────────────────────────────────────────────
ARCHITECTURAL_VOCAB = [
    # Special tokens
    "<PAD>", "<SOS>", "<EOS>", "<UNK>",

    # Articles / prepositions (French)
    "le", "la", "les", "un", "une", "des", "de", "du", "d", "l",
    "avec", "et", "sur", "dans", "entre", "vers", "par", "pour",
    "au", "aux", "en", "à", "est", "sont", "a", "ont",
    "ce", "cette", "ces", "se", "qui", "que", "dont",
    "comprend", "comprenant", "dispose", "disposant",
    "situé", "situés", "sitée", "sitées",
    "orienté", "orientés", "orientée", "orientées",

    # Room types
    "salon", "séjour", "cuisine", "chambre", "salle", "bain", "douche",
    "toilettes", "wc", "bureau", "bibliothèque", "dressing", "placard",
    "couloir", "entrée", "hall", "vestibule", "garage", "cave",
    "terrasse", "balcon", "loggia", "véranda", "jardin", "patio",
    "buanderie", "cellier", "débarras", "grenier", "sous-sol",
    "séjour-cuisine", "living", "open-space",

    # Surfaces
    "m²", "mètres", "carrés", "surface", "superficie", "espace",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "12", "14", "15", "16", "18", "20", "22", "24", "25",
    "28", "30", "32", "35", "40", "45", "50", "60", "80", "100",
    "120", "140", "150", "180", "200",

    # Openings
    "fenêtre", "fenêtres", "porte", "portes", "baie", "vitrée",
    "ouverture", "ouvertures", "accès", "passage", "coulissante",
    "double", "simple", "triple", "exposition",

    # Orientation
    "nord", "sud", "est", "ouest", "nord-est", "nord-ouest",
    "sud-est", "sud-ouest", "principale", "secondaire",

    # Style
    "moderne", "contemporain", "classique", "haussmannien", "industriel",
    "minimaliste", "scandinave", "méditerranéen", "bioclimatique",
    "traditionnel", "rustique", "loft", "duplex", "villa",

    # Architecture descriptors
    "plan", "résidentiel", "appartement", "maison", "logement",
    "étage", "rez-de-chaussée", "niveau", "niveaux",
    "pièce", "pièces", "habitable", "total", "totale",
    "lumineux", "lumineuse", "spacieux", "spacieuse",
    "ouvert", "ouverte", "fermé", "fermée",
    "distribution", "circulation", "agencement", "configuration",
    "principal", "principale", "secondaire",
    "adjacent", "adjacente", "attenant", "attenante",
    "direct", "directe", "indépendant", "indépendante",

    # Numbers as words
    "deux", "trois", "quatre", "cinq", "six", "sept", "huit",
    "neuf", "dix", "onze", "douze",

    # Connectors
    "ainsi", "également", "notamment", "dont", "soit",
    "comprenant", "incluant", "offrant", "permettant",
]


class Vocabulary:
    """Maps tokens ↔ indices for the caption model."""

    PAD_IDX = 0
    SOS_IDX = 1
    EOS_IDX = 2
    UNK_IDX = 3

    def __init__(self, vocab: List[str] = None):
        if vocab is None:
            vocab = ARCHITECTURAL_VOCAB
        self.word2idx: Dict[str, int] = {w: i for i, w in enumerate(vocab)}
        self.idx2word: Dict[int, str] = {i: w for i, w in enumerate(vocab)}
        self.size = len(vocab)

    def encode(self, sentence: str) -> List[int]:
        """Tokenize and encode a sentence."""
        tokens = sentence.lower().replace(",", " ,").replace(".", " .").split()
        return (
            [self.SOS_IDX]
            + [self.word2idx.get(t, self.UNK_IDX) for t in tokens]
            + [self.EOS_IDX]
        )

    def decode(self, indices: List[int], skip_special: bool = True) -> str:
        """Decode a list of indices back to a sentence."""
        special = {self.PAD_IDX, self.SOS_IDX, self.EOS_IDX}
        words = []
        for idx in indices:
            if idx == self.EOS_IDX:
                break
            if skip_special and idx in special:
                continue
            words.append(self.idx2word.get(idx, "<UNK>"))
        return " ".join(words)

    def __len__(self):
        return self.size


# Singleton
vocab = Vocabulary()
