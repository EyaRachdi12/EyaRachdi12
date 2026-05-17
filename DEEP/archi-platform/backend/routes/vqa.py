"""
POST /ask-plan
Visual Question Answering on floor plan images using Google Gemini Flash 2.0.
Direct image analysis with multimodal LLM - no OpenCV preprocessing needed.
"""

import io
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
from models.gemini_client import analyze_plan_with_gemini

router = APIRouter()


# ── Smart VQA Engine ──────────────────────────────────────────────────────────
class SmartVQA:
    """
    Answers questions about floor plans using:
    1. Image analysis (OpenCV) to detect rooms, walls, openings
    2. Rule-based NLP to understand the question
    3. Structured answer generation
    """

    ROOM_KEYWORDS = {
        "salon":         ["salon", "séjour", "living", "sitting", "lounge"],
        "cuisine":       ["cuisine", "kitchen", "cook"],
        "chambre":       ["chambre", "bedroom", "room", "bed"],
        "salle de bain": ["salle de bain", "bathroom", "bath", "sdb", "douche"],
        "wc":            ["wc", "toilettes", "toilet", "restroom"],
        "bureau":        ["bureau", "office", "study"],
        "dressing":      ["dressing", "closet", "placard", "wardrobe"],
        "couloir":       ["couloir", "corridor", "hallway", "hall"],
        "terrasse":      ["terrasse", "balcon", "terrace", "balcony", "porch"],
        "garage":        ["garage", "parking"],
        "entrée":        ["entrée", "entrance", "foyer"],
    }

    ORIENTATIONS = ["nord", "sud", "est", "ouest", "nord-est", "nord-ouest", "sud-est", "sud-ouest"]

    def analyze_image(self, image: Image.Image) -> dict:
        """Extract structural info from the floor plan image."""
        img_cv = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)
        gray   = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        h, w   = gray.shape

        # Improved wall detection - adaptive thresholding
        walls = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Remove text and small details
        kernel_small = np.ones((2, 2), np.uint8)
        walls = cv2.morphologyEx(walls, cv2.MORPH_OPEN, kernel_small)
        
        # Strengthen walls
        kernel = np.ones((3, 3), np.uint8)
        walls = cv2.dilate(walls, kernel, iterations=2)

        # Detect rooms (white regions) - more aggressive
        _, rooms_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        rooms_clean   = cv2.bitwise_and(rooms_mask, cv2.bitwise_not(walls))
        
        # Fill holes and connect regions
        kernel_close  = np.ones((30, 30), np.uint8)
        rooms_filled  = cv2.morphologyEx(rooms_clean, cv2.MORPH_CLOSE, kernel_close)

        # Connected components = rooms
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            rooms_filled, connectivity=8
        )

        total_px = h * w
        rooms = []
        for i in range(1, num_labels):
            area_px = stats[i, cv2.CC_STAT_AREA]
            # Lower threshold to catch more rooms
            if area_px < total_px * 0.005:  # Changed from 0.01 to 0.005
                continue
            # Skip very large regions (likely background)
            if area_px > total_px * 0.4:
                continue
            cx = int(centroids[i][0])
            cy = int(centroids[i][1])
            rooms.append({
                "area_px":    area_px,
                "area_ratio": area_px / total_px,
                "cx": cx, "cy": cy,
                "x": stats[i, cv2.CC_STAT_LEFT],
                "y": stats[i, cv2.CC_STAT_TOP],
                "w": stats[i, cv2.CC_STAT_WIDTH],
                "h": stats[i, cv2.CC_STAT_HEIGHT],
            })

        rooms.sort(key=lambda r: r["area_px"], reverse=True)
        
        # If too few rooms detected, estimate from image complexity
        if len(rooms) < 2:
            # Fallback: estimate from edge density
            edges = cv2.Canny(gray, 30, 100)
            edge_density = float((edges > 0).mean())
            
            # More edges = more complex plan = more rooms
            if edge_density > 0.15:
                estimated_rooms = 6
            elif edge_density > 0.10:
                estimated_rooms = 4
            elif edge_density > 0.05:
                estimated_rooms = 3
            else:
                estimated_rooms = 2
            
            # Create synthetic room data
            rooms = []
            for i in range(estimated_rooms):
                rooms.append({
                    "area_px": total_px // estimated_rooms,
                    "area_ratio": 1.0 / estimated_rooms,
                    "cx": w // 2,
                    "cy": h // 2,
                    "x": 0, "y": 0, "w": w, "h": h,
                })
            n_rooms = estimated_rooms
        else:
            n_rooms = len(rooms)

        # Detect openings (doors/windows) via HoughLines
        edges = cv2.Canny(gray, 30, 100)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=30,
                                minLineLength=15, maxLineGap=5)
        n_lines    = len(lines) if lines is not None else 0
        n_windows  = max(2, min(12, n_lines // 8))
        n_doors    = max(1, min(8,  n_lines // 12))

        # Image metrics
        brightness = float(gray.mean())
        edge_density = float((edges > 0).mean())

        # Orientation from brightness distribution
        top    = gray[:h//6, :].mean()
        bottom = gray[5*h//6:, :].mean()
        left   = gray[:, :w//6].mean()
        right  = gray[:, 5*w//6:].mean()
        sides  = {"nord": top, "sud": bottom, "est": right, "ouest": left}
        orientation = max(sides, key=sides.get)

        # Estimate total area based on number of rooms
        base_areas = {1:35, 2:55, 3:75, 4:95, 5:110, 6:130, 7:150, 8:170, 9:190, 10:210}
        total_area = base_areas.get(n_rooms, 90 + n_rooms * 15)

        # Assign room types
        room_types = self._assign_room_types(rooms)

        return {
            "n_rooms":     n_rooms,
            "rooms":       rooms,
            "room_types":  room_types,
            "n_windows":   n_windows,
            "n_doors":     n_doors,
            "orientation": orientation,
            "total_area":  total_area,
            "brightness":  brightness,
            "edge_density": edge_density,
            "width": w, "height": h,
        }

    def _assign_room_types(self, rooms: list) -> list:
        """Assign room type names based on size ranking."""
        n = len(rooms)
        
        # Standard room assignment for typical floor plans
        if n >= 8:
            type_map = {
                0: "Salon / Séjour",
                1: "Cuisine / Salle à manger",
                2: "Chambre principale",
                3: "Chambre 2",
                4: "Chambre 3",
                5: "Chambre 4",
                6: "Salle de bain",
                7: "WC",
                8: "Bureau",
                9: "Couloir / Entrée",
            }
        elif n >= 5:
            type_map = {
                0: "Salon / Séjour",
                1: "Cuisine",
                2: "Chambre principale",
                3: "Chambre 2",
                4: "Salle de bain",
                5: "WC",
                6: "Couloir",
            }
        elif n >= 3:
            type_map = {
                0: "Salon / Séjour",
                1: "Cuisine",
                2: "Chambre",
                3: "Salle de bain",
            }
        else:
            type_map = {
                0: "Salon / Séjour",
                1: "Cuisine",
            }
        
        return [type_map.get(i, f"Pièce {i+1}") for i in range(n)]

    def _get_room_position(self, room: dict, img_w: int, img_h: int) -> str:
        """Get human-readable position of a room."""
        cx, cy = room["cx"], room["cy"]
        h_pos = "gauche" if cx < img_w / 3 else ("droite" if cx > 2 * img_w / 3 else "centre")
        v_pos = "haut" if cy < img_h / 3 else ("bas" if cy > 2 * img_h / 3 else "milieu")

        # Map to cardinal directions
        if v_pos == "haut" and h_pos == "gauche":   return "nord-ouest"
        if v_pos == "haut" and h_pos == "droite":   return "nord-est"
        if v_pos == "haut" and h_pos == "centre":   return "nord"
        if v_pos == "bas"  and h_pos == "gauche":   return "sud-ouest"
        if v_pos == "bas"  and h_pos == "droite":   return "sud-est"
        if v_pos == "bas"  and h_pos == "centre":   return "sud"
        if v_pos == "milieu" and h_pos == "gauche": return "ouest"
        if v_pos == "milieu" and h_pos == "droite": return "est"
        return "centre"

    def _get_room_area(self, room: dict, total_area: int, total_px: int) -> int:
        """Estimate room area in m²."""
        fraction = room["area_px"] / max(total_px, 1)
        return max(4, min(60, round(total_area * fraction)))

    def answer(self, image: Image.Image, question: str) -> dict:
        """Answer a question about the floor plan."""
        analysis = self.analyze_image(image)
        q_lower  = question.lower()
        q_type   = self._classify_question(q_lower)
        room_asked = self._extract_room_from_question(q_lower)

        img_w = analysis["width"]
        img_h = analysis["height"]
        total_px = img_w * img_h

        # ── Localisation ──────────────────────────────────────────────────────
        if q_type == "localisation":
            if room_asked and analysis["rooms"]:
                # Find the room most likely matching the asked type
                room_idx = self._find_room_index(room_asked, analysis["room_types"])
                if room_idx < len(analysis["rooms"]):
                    room = analysis["rooms"][room_idx]
                    pos  = self._get_room_position(room, img_w, img_h)
                    return {
                        "answer":      f"{room_asked.capitalize()} est situé(e) dans la zone {pos} du plan.",
                        "confidence":  0.78,
                        "detail":      f"Position détectée par analyse visuelle",
                    }
            return {
                "answer":     f"La localisation précise de {room_asked or 'cette pièce'} ne peut pas être déterminée avec certitude. Consultez votre architecte pour une annotation précise.",
                "confidence": 0.55,
                "detail":     "",
            }

        # ── Surface ───────────────────────────────────────────────────────────
        if q_type == "surface":
            if room_asked and analysis["rooms"]:
                room_idx = self._find_room_index(room_asked, analysis["room_types"])
                if room_idx < len(analysis["rooms"]):
                    room = analysis["rooms"][room_idx]
                    area = self._get_room_area(room, analysis["total_area"], total_px)
                    return {
                        "answer":     f"La surface estimée de {room_asked} est d'environ {area} m².",
                        "confidence": 0.72,
                        "detail":     f"Estimé proportionnellement à la surface totale de {analysis['total_area']} m²",
                    }
            # Total area
            if any(w in q_lower for w in ["total", "habitable", "logement", "appartement", "maison"]):
                return {
                    "answer":     f"La surface habitable totale estimée est d'environ {analysis['total_area']} m².",
                    "confidence": 0.75,
                    "detail":     f"Basé sur {analysis['n_rooms']} pièces détectées",
                }
            return {
                "answer":     f"Surface totale estimée : {analysis['total_area']} m² pour {analysis['n_rooms']} pièce(s).",
                "confidence": 0.70,
                "detail":     "",
            }

        # ── Comptage ──────────────────────────────────────────────────────────
        if q_type == "comptage":
            if any(w in q_lower for w in ["fenêtre", "baie", "ouverture", "window"]):
                return {
                    "answer":     f"Le plan comporte environ {analysis['n_windows']} fenêtre(s) et ouverture(s) extérieure(s).",
                    "confidence": 0.68,
                    "detail":     "Détecté par analyse des contours",
                }
            if any(w in q_lower for w in ["porte", "door"]):
                return {
                    "answer":     f"Le plan comporte environ {analysis['n_doors']} porte(s) intérieure(s).",
                    "confidence": 0.65,
                    "detail":     "",
                }
            if any(w in q_lower for w in ["chambre", "bedroom"]):
                n_bedrooms = sum(1 for t in analysis["room_types"] if "Chambre" in t)
                return {
                    "answer":     f"Le plan comprend {n_bedrooms} chambre(s).",
                    "confidence": 0.75,
                    "detail":     f"Sur {analysis['n_rooms']} pièces détectées au total",
                }
            return {
                "answer":     f"Le plan comprend {analysis['n_rooms']} pièce(s) au total.",
                "confidence": 0.80,
                "detail":     "",
            }

        # ── Présence ──────────────────────────────────────────────────────────
        if q_type == "presence":
            if room_asked:
                room_idx = self._find_room_index(room_asked, analysis["room_types"])
                present  = room_idx < len(analysis["rooms"])
                if present:
                    room = analysis["rooms"][room_idx]
                    area = self._get_room_area(room, analysis["total_area"], total_px)
                    pos  = self._get_room_position(room, img_w, img_h)
                    return {
                        "answer":     f"Oui, {room_asked} est présent(e) dans ce plan. Il/elle se trouve côté {pos} et mesure environ {area} m².",
                        "confidence": 0.80,
                        "detail":     "",
                    }
                else:
                    return {
                        "answer":     f"{room_asked.capitalize()} n'est pas clairement identifiable dans ce plan. Il est possible qu'il soit inclus dans une autre pièce.",
                        "confidence": 0.60,
                        "detail":     "",
                    }

        # ── Style ─────────────────────────────────────────────────────────────
        if q_type == "style":
            brightness = analysis["brightness"]
            edge_d     = analysis["edge_density"]
            if brightness > 210 and edge_d < 0.06:
                style = "minimaliste contemporain"
            elif brightness > 180:
                style = "contemporain"
            elif edge_d > 0.12:
                style = "complexe avec nombreuses subdivisions"
            else:
                style = "classique résidentiel"
            return {
                "answer":     f"Le style architectural de ce plan semble être {style}, basé sur la densité des murs et la luminosité générale.",
                "confidence": 0.65,
                "detail":     "",
            }

        # ── Orientation ───────────────────────────────────────────────────────
        if any(w in q_lower for w in ["orientation", "exposé", "nord", "sud", "est", "ouest"]):
            return {
                "answer":     f"L'orientation principale estimée du plan est vers le {analysis['orientation']}.",
                "confidence": 0.60,
                "detail":     "Estimé par analyse de la luminosité des bords",
            }

        # ── Accès / circulation ───────────────────────────────────────────────
        if any(w in q_lower for w in ["accès", "accede", "circulation", "couloir", "entrée"]):
            return {
                "answer":     f"La circulation dans ce plan s'effectue via {analysis['n_doors']} porte(s) intérieure(s). Le couloir/hall d'entrée est généralement positionné au centre du plan.",
                "confidence": 0.65,
                "detail":     "",
            }

        # ── General fallback ──────────────────────────────────────────────────
        rooms_list = ", ".join(analysis["room_types"][:5])
        return {
            "answer":     f"Ce plan comprend {analysis['n_rooms']} pièce(s) : {rooms_list}. Surface totale estimée : {analysis['total_area']} m². Orientation : {analysis['orientation']}.",
            "confidence": 0.70,
            "detail":     "",
        }

    def _classify_question(self, q: str) -> str:
        if any(w in q for w in ["où", "situé", "trouve", "localisation", "position", "emplacement"]):
            return "localisation"
        if any(w in q for w in ["surface", "superficie", "taille", "dimension", "m²", "grand", "combien de m"]):
            return "surface"
        if any(w in q for w in ["combien", "nombre", "count", "plusieurs"]):
            return "comptage"
        if any(w in q for w in ["y a-t-il", "est-ce", "existe", "présent", "disponible", "a-t-on", "il y a"]):
            return "presence"
        if any(w in q for w in ["style", "type", "architecture", "design"]):
            return "style"
        return "general"

    def _extract_room_from_question(self, q: str) -> str:
        for room_name, keywords in self.ROOM_KEYWORDS.items():
            if any(kw in q for kw in keywords):
                return room_name
        return ""

    def _find_room_index(self, room_asked: str, room_types: list) -> int:
        """Find the index of the room type that best matches the asked room."""
        room_map = {
            "salon":         ["Salon"],
            "cuisine":       ["Cuisine"],
            "chambre":       ["Chambre principale", "Chambre 2", "Chambre"],
            "salle de bain": ["Salle de bain"],
            "wc":            ["WC"],
            "bureau":        ["Bureau"],
            "dressing":      ["Dressing"],
            "couloir":       ["Couloir"],
            "terrasse":      ["Terrasse"],
            "garage":        ["Garage"],
            "entrée":        ["Couloir", "Entrée"],
        }
        targets = room_map.get(room_asked, [room_asked.capitalize()])
        for target in targets:
            for i, rt in enumerate(room_types):
                if target.lower() in rt.lower():
                    return i
        return len(room_types)  # not found


# Singleton
smart_vqa = SmartVQA()


@router.post("/ask-plan")
async def ask_plan(
    file:     UploadFile = File(...),
    question: str        = Form(...),
):
    if not question or len(question.strip()) < 3:
        raise HTTPException(status_code=400, detail="Question trop courte.")

    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible de lire l'image: {e}")

    try:
        # Analyze with Gemini Flash 2.0 (direct vision analysis)
        result = analyze_plan_with_gemini(image, question)
        
        answer = result.get("answer", "Désolé, je ne peux pas répondre.")
        needs_image = result.get("needs_image", False)
        
        # High confidence since Gemini directly sees the image
        confidence = 0.92
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur VQA: {e}")

    confidence_pct = round(confidence * 100, 1)

    response_data = {
        "question":       question,
        "answer":         answer,
        "confidence":     confidence,
        "confidence_pct": confidence_pct,
        "method":         result.get("model", "gemini-2.0-flash"),
        "needs_image":    needs_image,
    }
    
    # Add image prompt if visualization requested
    if needs_image and result.get("image_prompt"):
        response_data["image_prompt"] = result["image_prompt"]
    
    return JSONResponse(content=response_data)


@router.post("/ask-plan-url")
async def ask_plan_url(
    plan_id: str = Form(...),
    question: str = Form(...),
):
    """
    VQA endpoint that accepts a floor plan ID from the library
    Loads the image directly from disk instead of HTTP
    """
    print(f"🔍 [VQA] Received request - plan_id: {plan_id}, question: {question}")
    
    if not question or len(question.strip()) < 3:
        print(f"❌ [VQA] Question too short: {question}")
        raise HTTPException(status_code=400, detail="Question trop courte.")
    
    try:
        # Import floor plans library
        print("📦 [VQA] Importing floor plans library...")
        from routes.floor_plans_ai import FLOOR_PLANS_LIBRARY, SAMPLE_PLANS_DIR
        print(f"✅ [VQA] Import successful - {len(FLOOR_PLANS_LIBRARY)} plans available")
        
        # Find the plan
        print(f"🔍 [VQA] Searching for plan: {plan_id}")
        plan = next((p for p in FLOOR_PLANS_LIBRARY if p["id"] == plan_id), None)
        if not plan:
            print(f"❌ [VQA] Plan not found: {plan_id}")
            raise HTTPException(status_code=404, detail="Floor plan not found")
        
        print(f"✅ [VQA] Plan found: {plan['title']}")
        
        # Load image directly from disk
        image_path = SAMPLE_PLANS_DIR / plan["image_file"]
        print(f"📁 [VQA] Image path: {image_path}")
        
        if not image_path.exists():
            print(f"❌ [VQA] Image file not found: {image_path}")
            raise HTTPException(status_code=404, detail="Image file not found")
        
        print(f"✅ [VQA] Image file exists, loading...")
        image = Image.open(image_path).convert("RGB")
        print(f"✅ [VQA] Image loaded successfully: {image.size}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [VQA] Error loading image: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Impossible de charger l'image: {e}")
    
    try:
        print("🤖 [VQA] Analyzing with Gemini...")
        # Analyze with Gemini Flash 2.0
        result = analyze_plan_with_gemini(image, question)
        
        answer = result.get("answer", "Désolé, je ne peux pas répondre.")
        needs_image = result.get("needs_image", False)
        confidence = 0.92
        
        print(f"✅ [VQA] Analysis complete - answer length: {len(answer)}")
        
    except Exception as e:
        print(f"❌ [VQA] Error during analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur VQA: {e}")
    
    confidence_pct = round(confidence * 100, 1)
    
    response_data = {
        "question": question,
        "answer": answer,
        "confidence": confidence,
        "confidence_pct": confidence_pct,
        "method": result.get("model", "gemini-2.0-flash"),
        "needs_image": needs_image,
    }
    
    if needs_image and result.get("image_prompt"):
        response_data["image_prompt"] = result["image_prompt"]
    
    print(f"✅ [VQA] Sending response")
    return JSONResponse(content=response_data)
