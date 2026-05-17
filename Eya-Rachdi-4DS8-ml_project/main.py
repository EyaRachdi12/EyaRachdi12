from fastapi import FastAPI
from model_pipeline import (
    prepare_data,
    train_model,
    evaluate_model,
    save_model,
    load_model,
)
import argparse
import subprocess
import sys
import mlflow
import mlflow.sklearn

# -------------------------
#   FASTAPI POUR DOCKER
# -------------------------
app = FastAPI(title="HR Attrition ML API")

@app.get("/")
def read_root():
    return {"message": "Pipeline ML prêt et FastAPI actif !"}


# -------------------------
#   CONFIGURATION MLFLOW
# -------------------------
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("HR-Attrition-Project")


def run_security_scan():
    """Exécute une analyse de sécurité Bandit"""
    print("\n Analyse de sécurité avec Bandit...")
    try:
        subprocess.run(["bandit", "-r", ".", "-q"], check=True)
        print(" Analyse de sécurité terminée : aucun problème critique détecté.")
    except subprocess.CalledProcessError:
        print("Bandit a détecté des problèmes de sécurité.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline Machine Learning")

    parser.add_argument("--prepare", action="store_true", help="Préparer les données")
    parser.add_argument("--train", action="store_true", help="Entraîner le modèle")
    parser.add_argument("--evaluate", action="store_true", help="Évaluer le modèle")
    parser.add_argument("--save", action="store_true", help="Sauvegarder le modèle")
    parser.add_argument("--security-check", action="store_true", help="Scan sécurité")
    parser.add_argument("--all", action="store_true", help="Exécuter tout le pipeline")

    args = parser.parse_args()

    DATA_FILE = "WA_Fn-UseC_-HR-Employee-Attrition.csv"
    MODEL_FILE = "decision_tree_model.joblib"

    # -------------------------
    #   RUN GLOBAL MLFLOW
    # -------------------------
    with mlflow.start_run(run_name="Full_HR_Attrition_Pipeline"):

        # Scan sécurité
        if args.security_check:
            run_security_scan()

        # Préparation
        if args.prepare or args.all:
            print("\n📦 Préparation des données...")
            X_train, X_test, y_train, y_test = prepare_data(DATA_FILE)
            print("✅ Préparation terminée !")

        # Entraînement
        if args.train or args.all:
            print("\n🚀 Entraînement du modèle...")
            X_train, X_test, y_train, y_test = prepare_data(DATA_FILE)

            # Paramètres MLflow
            max_depth = 5
            random_state = 42

            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("random_state", random_state)

            model = train_model(X_train, y_train)
            save_model(model, MODEL_FILE)

            print(f"✅ Modèle entraîné et sauvegardé sous {MODEL_FILE} !")

        # Évaluation
        if args.evaluate or args.all:
            print("\n📊 Évaluation du modèle...")
            model = load_model(MODEL_FILE)

            X_train, X_test, y_train, y_test = prepare_data(DATA_FILE)

            # récupérer les métriques ICI
            metrics = evaluate_model(model, X_test, y_test)

            # les logger dans MLflow
            for name, value in metrics.items():
                mlflow.log_metric(name, value)

            print("✅ Évaluation terminée !")

        # Sauvegarde seule
        if args.save:
            print("\n💾 Sauvegarde du modèle...")
            model = load_model(MODEL_FILE)
            save_model(model, MODEL_FILE)
            print("✅ Modèle sauvegardé !")
