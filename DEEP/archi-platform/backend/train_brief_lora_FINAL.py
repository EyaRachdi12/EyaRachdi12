# ============================================================
# CELL 1 - Mount Google Drive (RUN THIS FIRST!)
# ============================================================
from google.colab import drive
drive.mount('/content/drive')

# Verify drive is mounted
import os
print("Drive mounted!")
print("Files in MyDrive:", os.listdir('/content/drive/MyDrive')[:5])


# ============================================================
# CELL 2 - Install dependencies (NO bitsandbytes!)
# ============================================================
import subprocess
subprocess.run(["pip", "install", "-q", "transformers==4.40.0"], check=True)
subprocess.run(["pip", "install", "-q", "peft==0.10.0"], check=True)
subprocess.run(["pip", "install", "-q", "accelerate==0.29.0"], check=True)
subprocess.run(["pip", "install", "-q", "datasets==2.18.0"], check=True)
subprocess.run(["pip", "install", "-q", "trl==0.8.1"], check=True)

import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    print("WARNING: No GPU! Go to Runtime > Change runtime type > T4 GPU")


# ============================================================
# CELL 3 - Generate 50 diverse training examples
# ============================================================
import json

training_data = [
  {
    "input": "Je veux construire une maison moderne pour ma famille de 4 personnes. Grande cuisine ouverte sur le salon, 3 chambres dont une suite parentale avec dressing. Beaucoup de fenetres. Budget 400 000 euros, terrain 800m2. Terrasse pour barbecue.",
    "output": '{"surface_souhaitee": "120-140 m2", "budget": "350000-450000", "style": "Contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-35 m2", "details": "Ouvert sur cuisine, lumineux"}, {"nom": "Cuisine", "surface": "15-20 m2", "details": "Semi-ouverte, ilot central"}, {"nom": "Chambre principale", "surface": "20-25 m2", "details": "Suite avec dressing"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Terrasse", "surface": "20 m2"}]}'
  },
  {
    "input": "Petite maison pour couple, environ 80m2. 2 chambres, cuisine fonctionnelle, petit jardin. Budget 250 000 euros. Style simple et pratique.",
    "output": '{"surface_souhaitee": "70-90 m2", "budget": "220000-280000", "style": "Fonctionnel", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "25-30 m2"}, {"nom": "Cuisine", "surface": "10-12 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Jardin", "surface": "50 m2"}]}'
  },
  {
    "input": "Villa de luxe pour famille nombreuse, 6 personnes. 5 chambres, grande piscine, home cinema, bureau. Style contemporain haut de gamme. Budget 800 000 euros, terrain 1500m2.",
    "output": '{"surface_souhaitee": "200-250 m2", "budget": "750000-850000", "style": "Contemporain luxe", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "50-60 m2", "details": "Double hauteur"}, {"nom": "Cuisine", "surface": "25-30 m2", "details": "Ilot central, equipee"}, {"nom": "Chambre principale", "surface": "30-35 m2", "details": "Suite parentale"}, {"nom": "Chambre 2", "surface": "16-18 m2"}, {"nom": "Chambre 3", "surface": "16-18 m2"}, {"nom": "Chambre 4", "surface": "14-16 m2"}, {"nom": "Chambre 5", "surface": "14-16 m2"}, {"nom": "Bureau", "surface": "15-18 m2"}, {"nom": "Home cinema", "surface": "20-25 m2"}, {"nom": "Piscine", "surface": "40 m2"}]}'
  },
  {
    "input": "Appartement familial 120m2, 3 chambres, terrasse, quartier calme. Budget 400 000 euros. Style moderne.",
    "output": '{"surface_souhaitee": "110-130 m2", "budget": "370000-430000", "style": "Moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-35 m2"}, {"nom": "Cuisine", "surface": "12-15 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Terrasse", "surface": "15-20 m2"}]}'
  },
  {
    "input": "Maison ecologique passive, 100m2, 2 chambres, bureau, jardin potager. Materiaux naturels, panneaux solaires. Budget 320 000 euros.",
    "output": '{"surface_souhaitee": "90-110 m2", "budget": "290000-350000", "style": "Ecologique/Passif", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "28-32 m2", "details": "Orientation sud"}, {"nom": "Cuisine", "surface": "12-14 m2", "details": "Ouverte"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Bureau", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "7-9 m2"}, {"nom": "Jardin potager", "surface": "30 m2"}]}'
  },
  {
    "input": "Loft industriel 90m2 pour jeune couple, espace ouvert, 1 chambre, mezzanine, cuisine americaine. Budget 280 000 euros. Style industriel.",
    "output": '{"surface_souhaitee": "80-100 m2", "budget": "250000-310000", "style": "Industriel/Loft", "pieces_souhaitees": [{"nom": "Espace principal ouvert", "surface": "50-60 m2", "details": "Salon+cuisine americaine"}, {"nom": "Chambre", "surface": "16-18 m2"}, {"nom": "Mezzanine", "surface": "15-20 m2", "details": "Bureau ou espace detente"}, {"nom": "Salle de bain", "surface": "8-10 m2"}]}'
  },
  {
    "input": "Maison traditionnelle provencale, 150m2, 4 chambres, piscine, garage double. Tuiles, pierre apparente. Budget 550 000 euros.",
    "output": '{"surface_souhaitee": "140-160 m2", "budget": "500000-600000", "style": "Traditionnel provencal", "pieces_souhaitees": [{"nom": "Salon", "surface": "30-35 m2"}, {"nom": "Salle a manger", "surface": "20-25 m2"}, {"nom": "Cuisine", "surface": "15-18 m2"}, {"nom": "Chambre principale", "surface": "20-22 m2", "details": "Avec salle de bain"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Piscine", "surface": "30 m2"}, {"nom": "Garage", "surface": "40 m2", "details": "Double"}]}'
  },
  {
    "input": "Studio etudiant 30m2, kitchenette, salle de bain, rangements optimises. Budget 120 000 euros. Centre ville.",
    "output": '{"surface_souhaitee": "28-35 m2", "budget": "100000-140000", "style": "Compact/Optimise", "pieces_souhaitees": [{"nom": "Piece principale", "surface": "20-22 m2", "details": "Salon+chambre+kitchenette"}, {"nom": "Salle de bain", "surface": "4-5 m2"}, {"nom": "Rangements", "surface": "2-3 m2"}]}'
  },
  {
    "input": "Maison plain-pied pour seniors, 90m2, 2 chambres, tout accessible PMR, grande salle de bain. Jardin de plain-pied. Budget 300 000 euros.",
    "output": '{"surface_souhaitee": "85-100 m2", "budget": "270000-330000", "style": "Accessible/Plain-pied", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "28-32 m2"}, {"nom": "Cuisine", "surface": "12-14 m2", "details": "Accessible PMR"}, {"nom": "Chambre principale", "surface": "16-18 m2", "details": "Acces fauteuil"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Grande salle de bain", "surface": "10-12 m2", "details": "Douche italienne PMR"}, {"nom": "Jardin", "surface": "100 m2", "details": "De plain-pied"}]}'
  },
  {
    "input": "Chalet montagne 130m2, 5 chambres, grande cheminee, sauna, garage ski. Bois et pierre. Budget 600 000 euros.",
    "output": '{"surface_souhaitee": "120-140 m2", "budget": "550000-650000", "style": "Chalet montagne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "40-45 m2", "details": "Grande cheminee"}, {"nom": "Cuisine", "surface": "15-18 m2"}, {"nom": "Chambre principale", "surface": "18-20 m2"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Chambre 5", "surface": "10-12 m2"}, {"nom": "Sauna", "surface": "8-10 m2"}, {"nom": "Garage ski", "surface": "20-25 m2"}]}'
  },
  {
    "input": "Maison contemporaine 160m2, 4 chambres, bureau, salle de sport, piscine interieure. Budget 900 000 euros. Style minimaliste.",
    "output": '{"surface_souhaitee": "150-170 m2", "budget": "850000-950000", "style": "Minimaliste contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "40-50 m2"}, {"nom": "Cuisine", "surface": "20-25 m2"}, {"nom": "Chambre principale", "surface": "25-30 m2", "details": "Suite avec dressing"}, {"nom": "Chambre 2", "surface": "16-18 m2"}, {"nom": "Chambre 3", "surface": "14-16 m2"}, {"nom": "Chambre 4", "surface": "14-16 m2"}, {"nom": "Bureau", "surface": "15-18 m2"}, {"nom": "Salle de sport", "surface": "20-25 m2"}, {"nom": "Piscine interieure", "surface": "40-50 m2"}]}'
  },
  {
    "input": "Maison bois 110m2, 3 chambres, veranda, poele a bois, jardin 500m2. Budget 350 000 euros. Style scandinave.",
    "output": '{"surface_souhaitee": "100-120 m2", "budget": "320000-380000", "style": "Scandinave/Bois", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-35 m2", "details": "Poele a bois"}, {"nom": "Cuisine", "surface": "12-15 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Veranda", "surface": "15-20 m2"}, {"nom": "Jardin", "surface": "500 m2"}]}'
  },
  {
    "input": "Duplex 140m2, 4 chambres, 2 salles de bain, terrasse rooftop, parking. Budget 480 000 euros. Style urbain moderne.",
    "output": '{"surface_souhaitee": "130-150 m2", "budget": "450000-510000", "style": "Urbain moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "35-40 m2"}, {"nom": "Cuisine", "surface": "14-16 m2"}, {"nom": "Chambre principale", "surface": "18-20 m2"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "10-12 m2"}, {"nom": "Salle de bain 1", "surface": "8-10 m2"}, {"nom": "Salle de bain 2", "surface": "6-8 m2"}, {"nom": "Terrasse rooftop", "surface": "30-40 m2"}, {"nom": "Parking", "surface": "15 m2"}]}'
  },
  {
    "input": "Maison familiale 180m2, 5 chambres, grande salle de jeux enfants, bureau parental, 2 salles de bain, garage. Budget 650 000 euros.",
    "output": '{"surface_souhaitee": "170-190 m2", "budget": "600000-700000", "style": "Familial contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "40-45 m2"}, {"nom": "Cuisine", "surface": "18-22 m2"}, {"nom": "Chambre principale", "surface": "22-25 m2", "details": "Suite parentale"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "14-16 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Chambre 5", "surface": "12-14 m2"}, {"nom": "Salle de jeux", "surface": "20-25 m2"}, {"nom": "Bureau", "surface": "12-15 m2"}, {"nom": "Salle de bain 1", "surface": "9-11 m2"}, {"nom": "Salle de bain 2", "surface": "7-9 m2"}, {"nom": "Garage", "surface": "20 m2"}]}'
  },
  {
    "input": "Maison de ville 75m2 sur 3 niveaux, 2 chambres, terrasse, cave. Budget 350 000 euros. Style haussmannien renove.",
    "output": '{"surface_souhaitee": "70-85 m2", "budget": "320000-380000", "style": "Haussmannien renove", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "22-26 m2"}, {"nom": "Cuisine", "surface": "10-12 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Terrasse", "surface": "10-15 m2"}, {"nom": "Cave", "surface": "10-15 m2"}]}'
  },
  {
    "input": "Maison architecte 200m2, 4 chambres, patio central, toit terrasse, domotique complete. Budget 1 000 000 euros. Style contemporain signature.",
    "output": '{"surface_souhaitee": "190-210 m2", "budget": "950000-1050000", "style": "Contemporain signature", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "50-60 m2", "details": "Vue sur patio"}, {"nom": "Cuisine", "surface": "25-30 m2", "details": "Professionnelle"}, {"nom": "Chambre principale", "surface": "30-35 m2", "details": "Suite complete"}, {"nom": "Chambre 2", "surface": "18-20 m2"}, {"nom": "Chambre 3", "surface": "16-18 m2"}, {"nom": "Chambre 4", "surface": "14-16 m2"}, {"nom": "Patio central", "surface": "30-40 m2"}, {"nom": "Toit terrasse", "surface": "50-60 m2"}, {"nom": "Salle de bain principale", "surface": "15-18 m2"}]}'
  },
  {
    "input": "Renovation maison ancienne 95m2, garder le cachet, 3 chambres, salle de bain moderne, isolation thermique. Budget 280 000 euros.",
    "output": '{"surface_souhaitee": "90-100 m2", "budget": "250000-310000", "style": "Ancien renove", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "28-32 m2", "details": "Poutres apparentes"}, {"nom": "Cuisine", "surface": "12-14 m2", "details": "Moderne dans cadre ancien"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2", "details": "Moderne"}]}'
  },
  {
    "input": "Maison bioclimatique 125m2, 3 chambres, serre bioclimatique, toiture vegetalisee, recup eau pluie. Budget 420 000 euros.",
    "output": '{"surface_souhaitee": "115-135 m2", "budget": "390000-450000", "style": "Bioclimatique", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "32-36 m2", "details": "Orientation sud"}, {"nom": "Cuisine", "surface": "14-16 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Serre bioclimatique", "surface": "15-20 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}]}'
  },
  {
    "input": "Penthouse 170m2, 3 chambres, grande terrasse panoramique, jacuzzi exterieur, cave a vin. Budget 1 200 000 euros. Vue mer.",
    "output": '{"surface_souhaitee": "160-180 m2", "budget": "1100000-1300000", "style": "Luxe/Penthouse", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "50-60 m2", "details": "Vue panoramique"}, {"nom": "Cuisine", "surface": "20-25 m2", "details": "Ouverte, equipee"}, {"nom": "Chambre principale", "surface": "25-30 m2", "details": "Suite avec vue"}, {"nom": "Chambre 2", "surface": "16-18 m2"}, {"nom": "Chambre 3", "surface": "14-16 m2"}, {"nom": "Terrasse panoramique", "surface": "60-80 m2"}, {"nom": "Jacuzzi", "surface": "8-10 m2", "details": "Exterieur"}, {"nom": "Cave a vin", "surface": "10-12 m2"}]}'
  },
  {
    "input": "Maison container 85m2, 2 chambres, toit terrasse, design industriel. Budget 200 000 euros. Style alternatif.",
    "output": '{"surface_souhaitee": "80-95 m2", "budget": "180000-220000", "style": "Container/Industriel", "pieces_souhaitees": [{"nom": "Espace de vie ouvert", "surface": "40-45 m2", "details": "Salon+cuisine"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Toit terrasse", "surface": "40-50 m2"}]}'
  },
  {
    "input": "Maison neuve 135m2, 4 chambres, garage, jardin clos, proche ecoles. Budget 450 000 euros. Style pavillonnaire moderne.",
    "output": '{"surface_souhaitee": "125-145 m2", "budget": "420000-480000", "style": "Pavillonnaire moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "32-36 m2"}, {"nom": "Cuisine", "surface": "14-16 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Garage", "surface": "20-25 m2"}, {"nom": "Jardin", "surface": "200 m2"}]}'
  },
  {
    "input": "Maison bord de mer 110m2, 3 chambres, grande terrasse vue ocean, douche exterieure. Budget 500 000 euros. Style balneare.",
    "output": '{"surface_souhaitee": "100-120 m2", "budget": "470000-530000", "style": "Balneare/Bord de mer", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "35-40 m2", "details": "Vue ocean"}, {"nom": "Cuisine", "surface": "14-16 m2", "details": "Ouverte"}, {"nom": "Chambre principale", "surface": "18-20 m2", "details": "Vue mer"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Grande terrasse", "surface": "30-40 m2"}, {"nom": "Douche exterieure", "surface": "3-4 m2"}]}'
  },
  {
    "input": "Appartement 55m2, 2 chambres, balcon, cave, parking. Budget 220 000 euros. Style moderne epure.",
    "output": '{"surface_souhaitee": "50-60 m2", "budget": "200000-240000", "style": "Moderne epure", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "20-24 m2"}, {"nom": "Cuisine", "surface": "8-10 m2"}, {"nom": "Chambre principale", "surface": "12-14 m2"}, {"nom": "Chambre 2", "surface": "9-11 m2"}, {"nom": "Salle de bain", "surface": "5-7 m2"}, {"nom": "Balcon", "surface": "6-8 m2"}, {"nom": "Cave", "surface": "5 m2"}]}'
  },
  {
    "input": "Maison 145m2, 4 chambres, bureau, salle de bain parentale, jardin avec abri de jardin. Budget 520 000 euros. Style contemporain.",
    "output": '{"surface_souhaitee": "135-155 m2", "budget": "490000-550000", "style": "Contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "36-40 m2"}, {"nom": "Cuisine", "surface": "16-18 m2"}, {"nom": "Chambre principale", "surface": "20-22 m2", "details": "Avec salle de bain"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Bureau", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Jardin", "surface": "150 m2"}]}'
  },
  {
    "input": "Maison 60m2 pour investissement locatif, 2 chambres, fonctionnel, facile a entretenir. Budget 180 000 euros.",
    "output": '{"surface_souhaitee": "55-65 m2", "budget": "160000-200000", "style": "Fonctionnel/Locatif", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "20-24 m2"}, {"nom": "Cuisine", "surface": "8-10 m2"}, {"nom": "Chambre 1", "surface": "12-14 m2"}, {"nom": "Chambre 2", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "5-7 m2"}]}'
  },
  {
    "input": "Maison neuve 105m2, 3 chambres, cuisine americaine, salon lumineux, garage, jardin 300m2. Budget 370 000 euros. Style moderne.",
    "output": '{"surface_souhaitee": "95-115 m2", "budget": "340000-400000", "style": "Moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-34 m2", "details": "Cuisine americaine"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "7-9 m2"}, {"nom": "Garage", "surface": "18-20 m2"}, {"nom": "Jardin", "surface": "300 m2"}]}'
  },
  {
    "input": "Appartement T4 90m2, 3 chambres, 2 salles de bain, grande terrasse 25m2, parking sous-sol. Budget 320 000 euros. Style contemporain.",
    "output": '{"surface_souhaitee": "85-95 m2", "budget": "295000-345000", "style": "Contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "28-32 m2"}, {"nom": "Cuisine", "surface": "10-12 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain 1", "surface": "7-9 m2"}, {"nom": "Salle de bain 2", "surface": "5-6 m2"}, {"nom": "Terrasse", "surface": "25 m2"}, {"nom": "Parking", "surface": "12 m2"}]}'
  },
  {
    "input": "Maison plain-pied 115m2, 3 chambres, grande cuisine ouverte, veranda, jardin plat 400m2. Budget 390 000 euros. Style contemporain.",
    "output": '{"surface_souhaitee": "105-125 m2", "budget": "360000-420000", "style": "Contemporain plain-pied", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "32-36 m2"}, {"nom": "Cuisine ouverte", "surface": "14-16 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Veranda", "surface": "18-22 m2"}, {"nom": "Jardin", "surface": "400 m2"}]}'
  },
  {
    "input": "Maison ossature bois 130m2, 4 chambres, poele a granules, panneaux solaires, jardin 600m2. Budget 430 000 euros. Style ecologique.",
    "output": '{"surface_souhaitee": "120-140 m2", "budget": "400000-460000", "style": "Ecologique/Ossature bois", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "32-36 m2", "details": "Poele a granules"}, {"nom": "Cuisine", "surface": "14-16 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "11-13 m2"}, {"nom": "Chambre 4", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Jardin", "surface": "600 m2"}]}'
  },
  {
    "input": "Villa moderne 220m2, 5 chambres, piscine chauffee, pool house, cuisine exterieure, domotique. Budget 1 100 000 euros.",
    "output": '{"surface_souhaitee": "210-230 m2", "budget": "1050000-1150000", "style": "Villa moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "55-65 m2"}, {"nom": "Cuisine", "surface": "25-30 m2"}, {"nom": "Chambre principale", "surface": "28-32 m2", "details": "Suite avec dressing"}, {"nom": "Chambre 2", "surface": "18-20 m2"}, {"nom": "Chambre 3", "surface": "16-18 m2"}, {"nom": "Chambre 4", "surface": "14-16 m2"}, {"nom": "Chambre 5", "surface": "14-16 m2"}, {"nom": "Piscine chauffee", "surface": "50 m2"}, {"nom": "Pool house", "surface": "25-30 m2"}, {"nom": "Cuisine exterieure", "surface": "15-20 m2"}]}'
  },
  {
    "input": "Maison de campagne 160m2, 5 chambres, grande grange renovee, ecurie, terrain 2 hectares. Budget 700 000 euros. Style rustique.",
    "output": '{"surface_souhaitee": "150-170 m2", "budget": "650000-750000", "style": "Rustique/Campagne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "40-50 m2", "details": "Cheminee en pierre"}, {"nom": "Cuisine", "surface": "20-25 m2", "details": "Rustique equipee"}, {"nom": "Chambre principale", "surface": "20-22 m2"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "14-16 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Chambre 5", "surface": "12-14 m2"}, {"nom": "Grange", "surface": "80-100 m2"}, {"nom": "Ecurie", "surface": "40-50 m2"}]}'
  },
  {
    "input": "T2 45m2 pour premier achat, 1 chambre, balcon, cave, proche transports. Budget 160 000 euros. Style moderne epure.",
    "output": '{"surface_souhaitee": "42-50 m2", "budget": "145000-175000", "style": "Moderne epure", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "18-22 m2"}, {"nom": "Cuisine", "surface": "7-9 m2"}, {"nom": "Chambre", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "4-6 m2"}, {"nom": "Balcon", "surface": "5-8 m2"}, {"nom": "Cave", "surface": "4-5 m2"}]}'
  },
  {
    "input": "Maison 175m2, 5 chambres, salle de jeux, bureau, 2 salles de bain, double garage, piscine. Budget 750 000 euros. Style contemporain.",
    "output": '{"surface_souhaitee": "165-185 m2", "budget": "700000-800000", "style": "Contemporain", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "42-48 m2"}, {"nom": "Cuisine", "surface": "18-22 m2"}, {"nom": "Chambre principale", "surface": "22-25 m2", "details": "Suite parentale"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "14-16 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Chambre 5", "surface": "12-14 m2"}, {"nom": "Salle de jeux", "surface": "18-22 m2"}, {"nom": "Bureau", "surface": "12-14 m2"}, {"nom": "Salle de bain 1", "surface": "9-11 m2"}, {"nom": "Salle de bain 2", "surface": "7-9 m2"}, {"nom": "Garage double", "surface": "40 m2"}, {"nom": "Piscine", "surface": "32 m2"}]}'
  },
  {
    "input": "Maison atypique 95m2, toit plat, grandes baies vitrees, 2 chambres, terrasse sur toit. Budget 340 000 euros. Style minimaliste.",
    "output": '{"surface_souhaitee": "88-105 m2", "budget": "310000-370000", "style": "Minimaliste", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-35 m2", "details": "Grandes baies vitrees"}, {"nom": "Cuisine", "surface": "12-14 m2", "details": "Ouverte"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "7-9 m2"}, {"nom": "Terrasse toit", "surface": "30-40 m2"}]}'
  },
  {
    "input": "Maison familiale 140m2, 4 chambres, cuisine equipee, buanderie, garage, jardin avec abri. Budget 490 000 euros.",
    "output": '{"surface_souhaitee": "130-150 m2", "budget": "460000-520000", "style": "Familial", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "34-38 m2"}, {"nom": "Cuisine equipee", "surface": "16-18 m2"}, {"nom": "Chambre principale", "surface": "18-20 m2"}, {"nom": "Chambre 2", "surface": "13-15 m2"}, {"nom": "Chambre 3", "surface": "12-14 m2"}, {"nom": "Chambre 4", "surface": "11-13 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Buanderie", "surface": "5-7 m2"}, {"nom": "Garage", "surface": "20 m2"}, {"nom": "Jardin", "surface": "200 m2"}]}'
  },
  {
    "input": "Appartement haussmannien 80m2 a renover, 2 chambres, parquet, moulures, cave. Budget 290 000 euros. Style classique renove.",
    "output": '{"surface_souhaitee": "75-85 m2", "budget": "265000-315000", "style": "Classique/Haussmannien", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "26-30 m2", "details": "Moulures, parquet"}, {"nom": "Cuisine", "surface": "10-12 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Cave", "surface": "6-8 m2"}]}'
  },
  {
    "input": "Maison 100m2 avec studio independant 25m2 pour parents ou location. 3 chambres principales, jardin. Budget 380 000 euros.",
    "output": '{"surface_souhaitee": "120-130 m2", "budget": "350000-410000", "style": "Contemporain avec annexe", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "28-32 m2"}, {"nom": "Cuisine", "surface": "12-14 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "7-9 m2"}, {"nom": "Studio independant", "surface": "25 m2", "details": "Entree separee"}, {"nom": "Jardin", "surface": "150 m2"}]}'
  },
  {
    "input": "Maison neuve RT2020, 120m2, 3 chambres, pompe a chaleur, triple vitrage, orientation bioclimatique. Budget 420 000 euros.",
    "output": '{"surface_souhaitee": "110-130 m2", "budget": "390000-450000", "style": "RT2020/Basse consommation", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "32-36 m2", "details": "Orientation sud"}, {"nom": "Cuisine", "surface": "13-15 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "11-13 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Cellier", "surface": "5-7 m2"}]}'
  },
  {
    "input": "Loft 120m2 dans ancienne usine, espace ouvert, 2 chambres en mezzanine, verriere industrielle. Budget 450 000 euros. Style industriel chic.",
    "output": '{"surface_souhaitee": "110-130 m2", "budget": "420000-480000", "style": "Industriel chic", "pieces_souhaitees": [{"nom": "Espace de vie principal", "surface": "60-70 m2", "details": "Salon+cuisine ouverte, verriere"}, {"nom": "Chambre 1 mezzanine", "surface": "18-22 m2"}, {"nom": "Chambre 2 mezzanine", "surface": "14-18 m2"}, {"nom": "Salle de bain", "surface": "9-11 m2"}, {"nom": "Dressing", "surface": "8-10 m2"}]}'
  },
  {
    "input": "Maison 85m2, 3 chambres, cuisine ouverte, salle de bain, WC separes, jardin 200m2. Budget 270 000 euros. Style simple.",
    "output": '{"surface_souhaitee": "80-92 m2", "budget": "248000-295000", "style": "Simple/Pratique", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "24-28 m2"}, {"nom": "Cuisine ouverte", "surface": "10-12 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "11-13 m2"}, {"nom": "Chambre 3", "surface": "9-11 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Jardin", "surface": "200 m2"}]}'
  },
  {
    "input": "Maison de retraite privee 300m2, 8 chambres individuelles, salle commune, infirmerie, jardin securise. Budget 900 000 euros.",
    "output": '{"surface_souhaitee": "280-320 m2", "budget": "850000-950000", "style": "Institutionnel/Residence", "pieces_souhaitees": [{"nom": "Salle commune", "surface": "60-70 m2"}, {"nom": "Cuisine collective", "surface": "25-30 m2"}, {"nom": "Chambre 1", "surface": "20-22 m2"}, {"nom": "Chambre 2", "surface": "20-22 m2"}, {"nom": "Chambre 3", "surface": "20-22 m2"}, {"nom": "Chambre 4", "surface": "20-22 m2"}, {"nom": "Chambre 5", "surface": "20-22 m2"}, {"nom": "Chambre 6", "surface": "20-22 m2"}, {"nom": "Chambre 7", "surface": "20-22 m2"}, {"nom": "Chambre 8", "surface": "20-22 m2"}, {"nom": "Infirmerie", "surface": "15-18 m2"}, {"nom": "Jardin securise", "surface": "200 m2"}]}'
  },
  {
    "input": "Maison 70m2 pour famille monoparentale, 2 chambres, bureau, jardin clos, proche ecole. Budget 240 000 euros.",
    "output": '{"surface_souhaitee": "65-78 m2", "budget": "220000-260000", "style": "Fonctionnel familial", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "22-26 m2"}, {"nom": "Cuisine", "surface": "9-11 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "10-12 m2"}, {"nom": "Bureau", "surface": "8-10 m2"}, {"nom": "Salle de bain", "surface": "6-7 m2"}, {"nom": "Jardin clos", "surface": "80 m2"}]}'
  },
  {
    "input": "Maison 155m2, 4 chambres, salle de bain parentale, dressing, bureau, cave a vin, garage. Budget 580 000 euros. Style classique moderne.",
    "output": '{"surface_souhaitee": "145-165 m2", "budget": "550000-610000", "style": "Classique moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "38-42 m2"}, {"nom": "Cuisine", "surface": "16-18 m2"}, {"nom": "Chambre principale", "surface": "22-25 m2", "details": "Avec salle de bain et dressing"}, {"nom": "Chambre 2", "surface": "14-16 m2"}, {"nom": "Chambre 3", "surface": "13-15 m2"}, {"nom": "Chambre 4", "surface": "12-14 m2"}, {"nom": "Bureau", "surface": "12-14 m2"}, {"nom": "Cave a vin", "surface": "8-10 m2"}, {"nom": "Garage", "surface": "20-22 m2"}]}'
  },
  {
    "input": "Maison 50m2 pour retraite, 1 chambre, tout de plain-pied, jardin facile d'entretien, proche commerces. Budget 190 000 euros.",
    "output": '{"surface_souhaitee": "45-55 m2", "budget": "170000-210000", "style": "Plain-pied compact", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "18-22 m2"}, {"nom": "Cuisine", "surface": "8-10 m2"}, {"nom": "Chambre", "surface": "14-16 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2", "details": "Douche italienne"}, {"nom": "Jardin", "surface": "60-80 m2", "details": "Facile entretien"}]}'
  },
  {
    "input": "Maison 190m2, 5 chambres, salle de cinema, salle de sport, piscine, double garage. Budget 950 000 euros. Style contemporain luxe.",
    "output": '{"surface_souhaitee": "180-200 m2", "budget": "900000-1000000", "style": "Contemporain luxe", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "48-55 m2"}, {"nom": "Cuisine", "surface": "22-26 m2"}, {"nom": "Chambre principale", "surface": "26-30 m2", "details": "Suite complete"}, {"nom": "Chambre 2", "surface": "16-18 m2"}, {"nom": "Chambre 3", "surface": "15-17 m2"}, {"nom": "Chambre 4", "surface": "14-16 m2"}, {"nom": "Chambre 5", "surface": "13-15 m2"}, {"nom": "Salle de cinema", "surface": "22-26 m2"}, {"nom": "Salle de sport", "surface": "20-24 m2"}, {"nom": "Piscine", "surface": "40 m2"}, {"nom": "Garage double", "surface": "40 m2"}]}'
  },
  {
    "input": "Maison 125m2, 3 chambres, grande cuisine familiale, buanderie, cellier, jardin 350m2 avec potager. Budget 410 000 euros.",
    "output": '{"surface_souhaitee": "115-135 m2", "budget": "380000-440000", "style": "Familial pratique", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "30-34 m2"}, {"nom": "Grande cuisine", "surface": "18-22 m2", "details": "Familiale"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "13-15 m2"}, {"nom": "Chambre 3", "surface": "11-13 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Buanderie", "surface": "5-7 m2"}, {"nom": "Cellier", "surface": "4-6 m2"}, {"nom": "Jardin avec potager", "surface": "350 m2"}]}'
  },
  {
    "input": "Maison 78m2, 2 chambres, bureau, terrasse couverte, pas de jardin. Budget 260 000 euros. Style moderne compact.",
    "output": '{"surface_souhaitee": "72-85 m2", "budget": "240000-280000", "style": "Moderne compact", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "24-28 m2"}, {"nom": "Cuisine", "surface": "9-11 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "10-12 m2"}, {"nom": "Bureau", "surface": "8-10 m2"}, {"nom": "Salle de bain", "surface": "6-8 m2"}, {"nom": "Terrasse couverte", "surface": "12-15 m2"}]}'
  },
  {
    "input": "Maison 165m2, 4 chambres, salle de bain par chambre, cuisine professionnelle, cave, garage triple. Budget 850 000 euros. Style luxe classique.",
    "output": '{"surface_souhaitee": "155-175 m2", "budget": "800000-900000", "style": "Luxe classique", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "44-50 m2"}, {"nom": "Cuisine professionnelle", "surface": "22-26 m2"}, {"nom": "Chambre 1 avec sdb", "surface": "24-28 m2"}, {"nom": "Chambre 2 avec sdb", "surface": "18-20 m2"}, {"nom": "Chambre 3 avec sdb", "surface": "16-18 m2"}, {"nom": "Chambre 4 avec sdb", "surface": "14-16 m2"}, {"nom": "Cave", "surface": "15-20 m2"}, {"nom": "Garage triple", "surface": "55-60 m2"}]}'
  },
  {
    "input": "Maison 108m2, 3 chambres, salon avec mezzanine, cuisine ouverte, salle de bain, jardin 250m2. Budget 360 000 euros. Style contemporain.",
    "output": '{"surface_souhaitee": "100-118 m2", "budget": "330000-390000", "style": "Contemporain", "pieces_souhaitees": [{"nom": "Salon avec mezzanine", "surface": "35-40 m2", "details": "Double hauteur"}, {"nom": "Cuisine ouverte", "surface": "13-15 m2"}, {"nom": "Chambre principale", "surface": "16-18 m2"}, {"nom": "Chambre 2", "surface": "12-14 m2"}, {"nom": "Chambre 3", "surface": "10-12 m2"}, {"nom": "Salle de bain", "surface": "8-10 m2"}, {"nom": "Jardin", "surface": "250 m2"}]}'
  },
  {
    "input": "Maison neuve 92m2, 3 chambres, cuisine semi-ouverte, salle de bain, WC separes, terrasse 12m2, jardin 180m2. Budget 310 000 euros. Style moderne.",
    "output": '{"surface_souhaitee": "85-100 m2", "budget": "285000-335000", "style": "Moderne", "pieces_souhaitees": [{"nom": "Salon/Sejour", "surface": "26-30 m2"}, {"nom": "Cuisine semi-ouverte", "surface": "11-13 m2"}, {"nom": "Chambre principale", "surface": "14-16 m2"}, {"nom": "Chambre 2", "surface": "11-13 m2"}, {"nom": "Chambre 3", "surface": "9-11 m2"}, {"nom": "Salle de bain", "surface": "7-9 m2"}, {"nom": "Terrasse", "surface": "12 m2"}, {"nom": "Jardin", "surface": "180 m2"}]}'
  }
]

print(f"Total training examples: {len(training_data)}")
print("Sample:")
print(json.dumps(training_data[0], ensure_ascii=False, indent=2)[:300])


# ============================================================
# CELL 4 - Format dataset for Phi-3 Mini
# ============================================================
from datasets import Dataset

SYSTEM_PROMPT = "Tu es un expert en architecture specialise dans l'analyse de briefs clients. Tu dois extraire et structurer les informations en JSON."

def format_example(example):
    return {
        "text": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nAnalyse ce brief client et genere une structure JSON detaillee.\n\nBrief: {example['input']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{example['output']}<|eot_id|>"
    }

formatted = [format_example(ex) for ex in training_data]
dataset = Dataset.from_list(formatted)

# Split: 80% train, 20% eval
dataset = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset = dataset["train"]
eval_dataset = dataset["test"]

print(f"Train examples: {len(train_dataset)}")
print(f"Eval examples:  {len(eval_dataset)}")
print(f"\nSample formatted text (first 400 chars):")
print(train_dataset[0]["text"][:400])


# ============================================================
# CELL 5 - Load Phi-3 Mini (NO quantization, FP16 only)
# ============================================================
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"

print(f"Loading {MODEL_NAME}...")
print("This takes ~3 minutes, please wait...")

# Confirm GPU before loading
if not torch.cuda.is_available():
    raise SystemExit("No GPU detected! Go to Runtime > Change runtime type > T4 GPU")
print(f"GPU confirmed: {torch.cuda.get_device_name(0)}")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    trust_remote_code=True
)
tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
    attn_implementation="eager"   # avoids flash-attention warning
)

model.config.use_cache = False
model.config.pretraining_tp = 1

print(f"\nModel loaded!")
print(f"Parameters: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B")
print(f"Device: {next(model.parameters()).device}")


# ============================================================
# CELL 6 - Configure LoRA
# ============================================================
from peft import LoraConfig, get_peft_model, TaskType

# CRITICAL: This fixes "element 0 of tensors does not require grad"
model.enable_input_require_grads()

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)

# CRITICAL: Cast LoRA trainable params to fp32 so gradients work correctly
for name, param in model.named_parameters():
    if param.requires_grad:
        param.data = param.data.float()  # fp32 for trainable params only

model.print_trainable_parameters()

# Verify
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"\nTrainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")


# ============================================================
# CELL 7 - Train the model
# ============================================================
from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datetime import datetime

# Save to Google Drive - PERMANENT STORAGE
OUTPUT_DIR = "/content/drive/MyDrive/phi3-brief-lora"

print(f"Model will be saved to: {OUTPUT_DIR}")

def tokenize_fn(examples):
    result = tokenizer(
        examples["text"],
        truncation=True,
        max_length=1024,
        padding=False
    )
    result["labels"] = result["input_ids"].copy()
    return result

tokenized_train = train_dataset.map(tokenize_fn, batched=True, remove_columns=["text"])
tokenized_eval  = eval_dataset.map(tokenize_fn,  batched=True, remove_columns=["text"])

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

use_fp16 = torch.cuda.is_available()
print(f"GPU available: {torch.cuda.is_available()}")
print(f"Using fp16: {use_fp16}")
if not use_fp16:
    print("WARNING: No GPU detected! Go to Runtime > Change runtime type > T4 GPU")
    raise SystemExit("Please enable GPU before training.")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=5,                  # More epochs with more data
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    gradient_accumulation_steps=8,       # Effective batch = 8
    learning_rate=2e-4,
    warmup_steps=20,
    logging_steps=10,
    evaluation_strategy="epoch",         # Eval after each epoch
    save_strategy="epoch",
    save_total_limit=2,                  # Keep only best 2 checkpoints
    load_best_model_at_end=True,         # Auto-load best checkpoint
    fp16=False,                          # ← model already loaded in fp16, don't double-apply
    bf16=False,
    optim="adamw_torch",                 # NO bitsandbytes!
    lr_scheduler_type="cosine",
    gradient_checkpointing=False,     # Must be False with PEFT/LoRA
    report_to="none",
    dataloader_pin_memory=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_eval,
    data_collator=data_collator,
)

print("\nStarting training...")
print(f"Train samples: {len(tokenized_train)}")
print(f"Eval samples:  {len(tokenized_eval)}")
print(f"Epochs: 5")
print(f"Estimated time: ~20-30 minutes on T4")
print("="*60)

start = datetime.now()
trainer.train()
duration = (datetime.now() - start).total_seconds() / 60

print(f"\nTraining complete in {duration:.1f} minutes!")


# ============================================================
# CELL 8 - Save model to Google Drive
# ============================================================
import os

OUTPUT_DIR = "/content/drive/MyDrive/phi3-brief-lora"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Saving LoRA adapters to {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

# Show saved files
files = os.listdir(OUTPUT_DIR)
total_size = sum(os.path.getsize(os.path.join(OUTPUT_DIR, f)) for f in files if os.path.isfile(os.path.join(OUTPUT_DIR, f)))
print(f"\nSaved files:")
for f in sorted(files):
    fpath = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fpath):
        print(f"  {f}  ({os.path.getsize(fpath)/1024/1024:.1f} MB)")
print(f"\nTotal size: {total_size/1024/1024:.1f} MB")
print("\nModel is safely saved in Google Drive!")
print("You can download it anytime from drive.google.com")


# ============================================================
# CELL 9 - Test the model
# ============================================================
import json

model.eval()

def test_model(brief_text, temperature=0.3):
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nTu es un expert en architecture specialise dans l'analyse de briefs clients. Tu dois extraire et structurer les informations en JSON.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nAnalyse ce brief client et genere une structure JSON detaillee.\n\nBrief: {brief_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=temperature,
            do_sample=(temperature > 0),
            top_p=0.9,
            repetition_penalty=1.1,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract only the assistant response (after last header)
    if "<|start_header_id|>assistant<|end_header_id|>" in response:
        response = response.split("<|start_header_id|>assistant<|end_header_id|>")[-1].strip()

    try:
        j_start = response.find("{")
        j_end = response.rfind("}") + 1
        return json.loads(response[j_start:j_end])
    except:
        return {"raw": response}

# Test with NEW briefs (not in training data)
test_cases = [
    "Maison moderne 120m2 pour famille de 4, 3 chambres, budget 400k euros",
    "Appartement 65m2, 2 chambres, balcon, budget 230 000 euros, style epure",
    "Grande villa 250m2, 6 chambres, piscine, tennis, budget 1 500 000 euros",
]

print("Testing model on NEW briefs (not seen during training):")
print("="*70)
for i, brief in enumerate(test_cases, 1):
    print(f"\nTest {i}: {brief}")
    print("-"*70)
    result = test_model(brief)
    print(json.dumps(result, ensure_ascii=False, indent=2))

print("\n" + "="*70)
print("Done! Check that:")
print("  - surface_souhaitee is in m2 (not ft2)")
print("  - budget is a number range in euros")
print("  - pieces_souhaitees is a list of rooms")
print("  - style matches the brief description")
