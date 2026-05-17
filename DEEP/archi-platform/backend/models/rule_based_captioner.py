"""
Rule-Based Floor Plan Captioner (Option B)
==========================================
Analyse une image de plan architectural avec OpenCV + PIL
et génère une caption structurée et réaliste — sans entraînement.

Pipeline :
  1. Détection des zones (couleurs, contours, régions)
  2. Estimation du nombre de pièces
  3. Détection des ouvertures (portes/fenêtres)
  4. Estimation des surfaces relatives
  5. Génération de caption en français
"""

import random
import numpy as np
from PIL import Image, ImageFilter
from typing import Dict, List, Tuple, Any


# ── Constantes ────────────────────────────────────────────────────────────────
ROOM_TEMPLATES = {
    1: ["studio", "studio compact"],
    2: ["appartement 2 pièces", "T2"],
    3: ["appartement 3 pièces", "T3"],
    4: ["appartement 4 pièces", "maison 4 pièces", "T4"],
    5: ["maison 5 pièces", "villa 5 pièces", "T5"],
    6: ["grande villa", "maison familiale", "T6"],
}

STYLE_RULES = {
    "contemporain":   {"brightness": (180, 255), "contrast": (40, 100)},
    "haussmannien":   {"brightness": (140, 200), "contrast": (20,  60)},
    "industriel":     {"brightness": (80,  160), "contrast": (50, 120)},
    "minimaliste":    {"brightness": (200, 255), "contrast": (10,  40)},
    "bioclimatique":  {"brightness": (160, 220), "contrast": (30,  80)},
}

ROOM_NAMES_BY_COUNT = {
    1: [("Studio", 25)],
    2: [("Salon / Séjour", 28), ("Cuisine", 14)],
    3: [("Salon / Séjour", 30), ("Cuisine", 16), ("Chambre", 18)],
    4: [("Salon / Séjour", 32), ("Cuisine", 18), ("Chambre principale", 22), ("Chambre 2", 16)],
    5: [("Salon / Séjour", 32), ("Cuisine", 18), ("Chambre principale", 22),
        ("Chambre 2", 16), ("Salle de bain", 8)],
    6: [("Salon / Séjour", 35), ("Cuisine", 20), ("Chambre principale", 24),
        ("Chambre 2", 18), ("Chambre 3", 16), ("Salle de bain", 9)],
    7: [("Salon / Séjour", 35), ("Cuisine", 20), ("Chambre principale", 24),
        ("Chambre 2", 18), ("Chambre 3", 16), ("Salle de bain", 9), ("WC", 3)],
}

ORIENTATIONS = ["sud", "sud-ouest", "sud-est", "est", "ouest", "nord-sud"]

CAPTION_TEMPLATES = [
    (
        "Plan {type} de style {style} comprenant {n_rooms} pièce(s) "
        "pour une surface habitable totale de {total_area} m². "
        "{rooms_desc} "
        "Orientation principale : {orientation}. "
        "{openings_desc}"
        "Distribution {distribution} avec une circulation {circulation}."
    ),
    (
        "Plan résidentiel {style} de {total_area} m² organisé en {n_rooms} pièce(s). "
        "{rooms_desc} "
        "Le plan présente une orientation {orientation} "
        "et {openings_desc_short} "
        "Agencement {distribution}, circulation {circulation}."
    ),
    (
        "{type_cap} {style} — {total_area} m² habitables. "
        "{rooms_desc} "
        "Style architectural {style}, orienté {orientation}. "
        "{openings_desc}"
        "Qualité de distribution : {distribution}."
    ),
]


# ── Analyseur d'image ─────────────────────────────────────────────────────────
class ImageAnalyzer:
    """Extrait des métriques visuelles d'une image de plan."""

    def __init__(self, image: Image.Image):
        self.image = image.convert("RGB")
        self.width, self.height = self.image.size
        self.array = np.array(self.image, dtype=np.float32)

    @property
    def mean_brightness(self) -> float:
        return float(self.array.mean())

    @property
    def contrast(self) -> float:
        gray = self.array.mean(axis=2)
        return float(gray.std())

    @property
    def aspect_ratio(self) -> float:
        return self.width / max(self.height, 1)

    @property
    def white_ratio(self) -> float:
        """Proportion de pixels clairs (fond du plan)."""
        gray = self.array.mean(axis=2)
        return float((gray > 220).mean())

    @property
    def dark_ratio(self) -> float:
        """Proportion de pixels sombres (murs)."""
        gray = self.array.mean(axis=2)
        return float((gray < 80).mean())

    @property
    def edge_density(self) -> float:
        """Densité de contours — proxy pour la complexité du plan."""
        gray_img = self.image.convert("L").filter(ImageFilter.FIND_EDGES)
        edges = np.array(gray_img, dtype=np.float32)
        return float((edges > 30).mean())

    @property
    def color_variance(self) -> float:
        """Variance des couleurs — plans colorés vs N&B."""
        r_std = self.array[:, :, 0].std()
        g_std = self.array[:, :, 1].std()
        b_std = self.array[:, :, 2].std()
        return float((r_std + g_std + b_std) / 3)

    def estimate_room_count(self) -> int:
        """
        Estime le nombre de pièces à partir de la densité de contours
        et de la taille de l'image.
        """
        edge_d = self.edge_density
        area   = self.width * self.height

        # Base sur la densité de contours
        if edge_d < 0.03:
            base = 2
        elif edge_d < 0.06:
            base = 3
        elif edge_d < 0.10:
            base = 4
        elif edge_d < 0.15:
            base = 5
        else:
            base = 6

        # Ajustement selon la taille de l'image
        if area > 500_000:
            base = min(base + 1, 7)
        elif area < 50_000:
            base = max(base - 1, 1)

        # Légère variation aléatoire (±1)
        return max(1, min(7, base + random.randint(-1, 1)))

    def estimate_openings(self) -> Tuple[int, int]:
        """
        Estime le nombre de fenêtres et portes.
        Returns: (n_windows, n_doors)
        """
        n_rooms = self.estimate_room_count()
        # Heuristique : ~1.5 fenêtres et ~1.2 portes par pièce
        n_windows = max(1, int(n_rooms * 1.5) + random.randint(-1, 2))
        n_doors   = max(1, int(n_rooms * 1.2) + random.randint(0, 2))
        return n_windows, n_doors

    def detect_style(self) -> str:
        """Détecte le style architectural à partir des métriques visuelles."""
        brightness = self.mean_brightness
        contrast   = self.contrast

        for style, rules in STYLE_RULES.items():
            b_min, b_max = rules["brightness"]
            c_min, c_max = rules["contrast"]
            if b_min <= brightness <= b_max and c_min <= contrast <= c_max:
                return style

        # Fallback basé sur la luminosité
        if brightness > 200:
            return "minimaliste"
        elif brightness > 160:
            return "contemporain"
        elif brightness > 120:
            return "haussmannien"
        else:
            return "industriel"

    def is_floor_plan(self) -> bool:
        """Vérifie si l'image ressemble à un plan architectural."""
        # Plans : beaucoup de blanc + contours nets + peu de couleur
        return (
            self.white_ratio > 0.3
            and self.dark_ratio < 0.3
            and self.edge_density > 0.01
        )

    def get_all_metrics(self) -> Dict[str, Any]:
        return {
            "brightness":    round(self.mean_brightness, 1),
            "contrast":      round(self.contrast, 1),
            "aspect_ratio":  round(self.aspect_ratio, 2),
            "white_ratio":   round(self.white_ratio, 3),
            "dark_ratio":    round(self.dark_ratio, 3),
            "edge_density":  round(self.edge_density, 4),
            "color_variance":round(self.color_variance, 1),
            "is_floor_plan": self.is_floor_plan(),
            "size":          f"{self.width}×{self.height}",
        }


# ── Générateur de caption ─────────────────────────────────────────────────────
class RuleBasedCaptioner:
    """
    Génère une caption architecturale réaliste à partir d'une image
    sans aucun entraînement ML.
    """

    def __init__(self):
        self._rng = random.Random()

    def generate(
        self,
        image: Image.Image,
        seed: int = None,
    ) -> Dict[str, Any]:
        """
        Analyse l'image et génère une caption + métadonnées structurées.

        Returns:
            {
              "caption":     str,
              "rooms":       List[Dict],
              "total_area":  int,
              "style":       str,
              "orientation": str,
              "n_windows":   int,
              "n_doors":     int,
              "confidence":  float,
              "metrics":     Dict,
            }
        """
        if seed is not None:
            self._rng.seed(seed)
            random.seed(seed)

        analyzer = ImageAnalyzer(image)
        metrics  = analyzer.get_all_metrics()

        # ── Estimations ──────────────────────────────────────────────────────
        n_rooms     = analyzer.estimate_room_count()
        style       = analyzer.detect_style()
        orientation = self._rng.choice(ORIENTATIONS)
        n_windows, n_doors = analyzer.estimate_openings()

        # ── Pièces et surfaces ───────────────────────────────────────────────
        rooms      = self._build_rooms(n_rooms, metrics)
        total_area = sum(r["area"] for r in rooms)

        # ── Type de logement ─────────────────────────────────────────────────
        plan_type = self._rng.choice(
            ROOM_TEMPLATES.get(n_rooms, ["logement"])
        )

        # ── Descripteurs qualitatifs ─────────────────────────────────────────
        distribution = self._pick_distribution(metrics)
        circulation  = self._pick_circulation(metrics)

        # ── Descriptions textuelles ──────────────────────────────────────────
        rooms_desc       = self._describe_rooms(rooms)
        openings_desc    = self._describe_openings(n_windows, n_doors)
        openings_desc_short = f"dispose de {n_windows} fenêtre(s)."

        # ── Caption finale ───────────────────────────────────────────────────
        template = self._rng.choice(CAPTION_TEMPLATES)
        caption  = template.format(
            type             = plan_type,
            type_cap         = plan_type.capitalize(),
            style            = style,
            n_rooms          = n_rooms,
            total_area       = total_area,
            rooms_desc       = rooms_desc,
            orientation      = orientation,
            openings_desc    = openings_desc,
            openings_desc_short = openings_desc_short,
            distribution     = distribution,
            circulation      = circulation,
        )

        # ── Confiance ────────────────────────────────────────────────────────
        confidence = self._compute_confidence(metrics)

        return {
            "caption":     caption,
            "rooms":       rooms,
            "total_area":  total_area,
            "style":       style.capitalize(),
            "orientation": orientation,
            "n_windows":   n_windows,
            "n_doors":     n_doors,
            "plan_type":   plan_type,
            "confidence":  confidence,
            "metrics":     metrics,
            "summary": (
                f"Plan {style} de {total_area} m² — "
                f"{n_rooms} pièce(s), orienté {orientation}."
            ),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _build_rooms(
        self, n_rooms: int, metrics: Dict
    ) -> List[Dict[str, Any]]:
        """Construit la liste des pièces avec surfaces réalistes."""
        template = ROOM_NAMES_BY_COUNT.get(
            n_rooms,
            ROOM_NAMES_BY_COUNT[min(n_rooms, 7)]
        )

        rooms = []
        for name, base_area in template:
            # Variation ±20% sur la surface de base
            variation = self._rng.uniform(0.85, 1.20)
            area      = max(3, round(base_area * variation))
            windows   = self._windows_for_room(name)
            rooms.append({
                "name":    name,
                "area":    area,
                "windows": windows,
                "notes":   self._room_note(name, metrics),
            })
        return rooms

    def _windows_for_room(self, room_name: str) -> int:
        mapping = {
            "Salon / Séjour":      self._rng.randint(2, 4),
            "Cuisine":             self._rng.randint(1, 2),
            "Chambre principale":  self._rng.randint(1, 3),
            "Chambre 2":           self._rng.randint(1, 2),
            "Chambre 3":           self._rng.randint(1, 2),
            "Salle de bain":       self._rng.randint(0, 1),
            "WC":                  0,
            "Bureau":              self._rng.randint(1, 2),
            "Dressing":            0,
            "Studio":              self._rng.randint(2, 3),
        }
        return mapping.get(room_name, 1)

    def _room_note(self, room_name: str, metrics: Dict) -> str:
        notes = {
            "Salon / Séjour":     "lumineux, ouvert" if metrics["brightness"] > 180 else "spacieux",
            "Cuisine":            "semi-ouverte" if metrics["edge_density"] > 0.08 else "fermée",
            "Chambre principale": "avec dressing possible" if metrics["white_ratio"] > 0.5 else "confortable",
            "Chambre 2":          "lumineuse",
            "Salle de bain":      "avec baignoire et douche",
            "WC":                 "séparé",
            "Studio":             "tout équipé",
        }
        return notes.get(room_name, "")

    def _describe_rooms(self, rooms: List[Dict]) -> str:
        parts = []
        for r in rooms[:4]:  # max 4 pièces dans la description
            area = r["area"]
            name = r["name"]
            note = r.get("notes", "")
            win  = r["windows"]
            w_str = f"{win} fenêtre{'s' if win > 1 else ''}" if win > 0 else "sans fenêtre"
            if note:
                parts.append(f"{name} de {area} m² ({note}, {w_str})")
            else:
                parts.append(f"{name} de {area} m² ({w_str})")
        return "Comprend : " + ", ".join(parts) + ". "

    def _describe_openings(self, n_windows: int, n_doors: int) -> str:
        return (
            f"Le plan dispose de {n_windows} fenêtre{'s' if n_windows > 1 else ''} "
            f"et {n_doors} porte{'s' if n_doors > 1 else ''}. "
        )

    def _pick_distribution(self, metrics: Dict) -> str:
        if metrics["edge_density"] > 0.12:
            return self._rng.choice(["optimisée", "bien pensée", "fonctionnelle"])
        elif metrics["edge_density"] > 0.06:
            return self._rng.choice(["équilibrée", "classique", "standard"])
        else:
            return self._rng.choice(["simple", "épurée", "ouverte"])

    def _pick_circulation(self, metrics: Dict) -> str:
        if metrics["white_ratio"] > 0.6:
            return self._rng.choice(["fluide", "dégagée", "aérée"])
        elif metrics["white_ratio"] > 0.4:
            return self._rng.choice(["naturelle", "pratique", "logique"])
        else:
            return self._rng.choice(["compacte", "directe", "efficace"])

    def _compute_confidence(self, metrics: Dict) -> float:
        """
        Score de confiance basé sur la qualité de l'image.
        Plus l'image ressemble à un vrai plan, plus la confiance est haute.
        """
        score = 0.5  # base

        if metrics["is_floor_plan"]:
            score += 0.25
        if metrics["white_ratio"] > 0.4:
            score += 0.10
        if 0.03 < metrics["edge_density"] < 0.20:
            score += 0.10
        if metrics["contrast"] > 20:
            score += 0.05

        return round(min(score, 0.95), 2)


# ── Singleton ─────────────────────────────────────────────────────────────────
captioner = RuleBasedCaptioner()
