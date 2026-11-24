"""
Clustering module (PRD Section 9.2): KMeans grouping cases by demographic/
geographic/temporal similarity, to surface groupings not specified in
advance (e.g. a cluster concentrated in one state during one season).

k is chosen by comparing Silhouette, Davies-Bouldin, and Calinski-Harabasz
across a small range of candidate k values (PRD Section 9.3), the same three
metrics Yang et al. (2024) used for a comparably scaled clustering problem.
"""
import os
import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

FEATURE_COLUMNS = ["age", "location_code", "visit_month", "diagnosis_code"]
SEED = 42
K_CANDIDATES = [3, 4, 5, 6, 7, 8]


def _prepare_features(df):
    return df[FEATURE_COLUMNS].fillna(-1)


def select_k(X_scaled):
    rows = []
    for k in K_CANDIDATES:
        km = KMeans(n_clusters=k, random_state=SEED, n_init=10)
        labels = km.fit_predict(X_scaled)
        rows.append({
            "k": k,
            "silhouette": silhouette_score(X_scaled, labels),
            "davies_bouldin": davies_bouldin_score(X_scaled, labels),
            "calinski_harabasz": calinski_harabasz_score(X_scaled, labels),
        })
    table = pd.DataFrame(rows).set_index("k")
    print("--- k selection ---")
    print(table)
    # Higher silhouette and Calinski-Harabasz are better; lower Davies-Bouldin is better.
    best_k = table["silhouette"].idxmax()
    print(f"Selected k = {best_k} (highest silhouette)")
    return best_k, table


def summarise_clusters(df, labels):
    df = df.copy()
    df["cluster"] = labels
    summary = df.groupby("cluster").agg(
        size=("patient_id", "count"),
        dominant_location=("location", lambda s: s.mode().iat[0]),
        dominant_diagnosis=("diagnosis", lambda s: s.mode().iat[0]),
        mean_age=("age", "mean"),
        dominant_month=("visit_month", lambda s: s.mode().iat[0]),
    ).round(1)
    print("--- Cluster summary ---")
    print(summary)
    return summary


def run():
    full_path = os.path.join(PROCESSED_DIR, "patient_records_clean.csv")
    df = pd.read_csv(full_path)

    X = _prepare_features(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k, k_table = select_k(X_scaled)
    model = KMeans(n_clusters=best_k, random_state=SEED, n_init=10)
    labels = model.fit_predict(X_scaled)

    summary = summarise_clusters(df, labels)

    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump({"model": model, "scaler": scaler, "k": best_k}, os.path.join(MODELS_DIR, "clustering_kmeans.joblib"))

    df["cluster"] = labels
    df.to_csv(os.path.join(PROCESSED_DIR, "patient_records_clustered.csv"), index=False)
    print(f"Saved clustering model and clustered dataset (k={best_k}).")
    return model, df, k_table, summary


if __name__ == "__main__":
    run()
