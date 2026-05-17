
# 1️⃣ mage de base légère
FROM python:3.11-slim

# 2️⃣ ariables d'environnement pour pip
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3️⃣ réer le répertoire de l'app
WORKDIR /app

# 4️⃣ opier uniquement requirements.txt pour profiter du cache Docker
COPY requirements.txt .

# 5️⃣ nstaller les dépendances sans cache pour réduire la taille
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 6️⃣pier le reste du code
COPY . .

# 7️⃣poser le port
EXPOSE 8000

# 8️⃣ommande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
