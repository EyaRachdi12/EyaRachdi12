# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os

# -----------------------------
#  Configuration FastAPI
# -----------------------------
app = FastAPI(title="Attrition Prediction API")

# -----------------------------
#  Chargement du modèle
# -----------------------------
MODEL_FILE = "decision_tree_model.joblib"

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"Le fichier modèle {MODEL_FILE} est introuvable !")

model = joblib.load(MODEL_FILE)


# -----------------------------
#  Schéma de données entrantes
# -----------------------------
class EmployeeData(BaseModel):
    Age: int
    DistanceFromHome: int
    MonthlyIncome: int
    JobSatisfaction: int
    WorkLifeBalance: int
    YearsAtCompany: int
    PerformanceRating: int
    OverTime_Yes: int = 0


# -----------------------------
# Schéma des hyperparamètres pour retrain()
# -----------------------------
class RetrainParams(BaseModel):
    max_depth: int = 5
    min_samples_split: int = 2


#  Fonction utilitaire pour préparer les données
# -----------------------------
def prepare_input(employee_dict, model):
    df = pd.DataFrame([employee_dict])

    # Ajouter les colonnes manquantes
    for col in model.feature_names_in_:
        if col not in df.columns:
            df[col] = 0

    # Réordonner
    df = df[model.feature_names_in_]
    return df


# -----------------------------
#  Route /predict
# -----------------------------
@app.post("/predict")
def predict(employee: EmployeeData):
    try:
        df = prepare_input(employee.dict(), model)
        prediction = model.predict(df)
        probability = model.predict_proba(df)[:, 1]

        return {"prediction": int(prediction[0]), "probability": float(probability[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Route /retrain
# -----------------------------
@app.post("/retrain")
def retrain(params: RetrainParams):
    try:
        CSV_FILE = (
            "/home/eya/Eya-Rachdi-4DS8-ml_project/WA_Fn-UseC_-HR-Employee-Attrition.csv"
        )

        if not os.path.exists(CSV_FILE):
            raise HTTPException(status_code=400, detail="Dataset introuvable !")

        df = pd.read_csv(CSV_FILE)

        # Suppression colonnes inutiles
        df = df.drop(
            columns=["EmployeeCount", "EmployeeNumber", "Over18", "StandardHours"],
            errors="ignore",
        )

        # Cible binaire
        df["Attrition"] = df["Attrition"].map({"Yes": 1, "No": 0})

        # Encodage OverTime
        df["OverTime_Yes"] = (df["OverTime"] == "Yes").astype(int)

        # Features utilisées
        FEATURES = [
            "Age",
            "DistanceFromHome",
            "MonthlyIncome",
            "JobSatisfaction",
            "WorkLifeBalance",
            "YearsAtCompany",
            "PerformanceRating",
            "OverTime_Yes",
        ]

        X = df[FEATURES]
        y = df["Attrition"]

        from sklearn.tree import DecisionTreeClassifier

        new_model = DecisionTreeClassifier(
            max_depth=params.max_depth, min_samples_split=params.min_samples_split
        )

        new_model.fit(X, y)

        # Sauvegarde
        joblib.dump(new_model, MODEL_FILE)

        return {
            "message": "Modèle réentraîné avec succès ✔️",
            "hyperparams_used": params.dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
#  Route test simple
# -----------------------------
@app.get("/")
def root():
    return {"message": "API ML Attrition fonctionne !"}
