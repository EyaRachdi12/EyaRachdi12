# model_pipeline.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import joblib


def prepare_data(filepath):
    """
    Charger et préparer les données.
    Retourne : X_train, X_test, y_train, y_test
    """
    df = pd.read_csv(filepath)

    # Séparer X et y
    X = df.drop("Attrition", axis=1)
    y = df["Attrition"]

    # Encodage des variables catégorielles
    X = pd.get_dummies(X, drop_first=True)

    # Standardisation des variables numériques
    num_cols = ["Age", "DistanceFromHome", "MonthlyIncome", "YearsAtCompany"]
    scaler = StandardScaler()
    X[num_cols] = scaler.fit_transform(X[num_cols])

    # Encoder la variable cible (Yes=1, No=0)
    y = y.map({"Yes": 1, "No": 0})

    # Découpage Train/Test
    return train_test_split(X, y, test_size=0.2, random_state=42)


def train_model(X_train, y_train):
    """
    Entraîner un modèle d’arbre de décision.
    Retourne : modèle entraîné
    """
    params = {
        "max_depth": 5,
        "criterion": "gini",
        "splitter": "best"
    }

    model = DecisionTreeClassifier(random_state=42, **params)
    model.fit(X_train, y_train)

    print("✔ Modèle entraîné.")
    return model


def evaluate_model(model, X_test, y_test):
    """
    Évaluer le modèle avec précision et matrice de confusion.
    Retourne : dictionnaire de métriques
    """
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"Accuracy: {acc:.2f}")
    print("Matrice de confusion :")
    print(cm)

    # Affichage visuel
    plt.figure(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title("Matrice de confusion - Decision Tree")
    plt.xlabel("Prédit")
    plt.ylabel("Réel")
    plt.savefig("confusion_matrix.png")  # remplacer plt.show() par savefig

    # Retourner les métriques
    metrics = {
        "accuracy": acc
    }
    return metrics



def save_model(model, filename="decision_tree_model.joblib"):
    joblib.dump(model, filename)
    print(f"Modèle sauvegardé sous {filename}")


def load_model(filename="decision_tree_model.joblib"):
    model = joblib.load(filename)
    print(f"Modèle chargé depuis {filename}")
    return model
