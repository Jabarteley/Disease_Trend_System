"""
Classification module (PRD Section 9.1): RandomForestClassifier predicting
the diagnosis category (diabetes / typhoid / malaria / none).

Feature note (document this in Chapter 4): clinical columns are
disease-specific (e.g. glucose is only recorded for diabetes work-ups,
malaria_parasite_grade only for malaria). Missing values are filled with -1
so the model can split on "was this test even ordered" as its own signal -
which is clinically realistic (the clinician already narrows down the
suspected disease before ordering a disease-specific test), not just
imputation noise. This is called out explicitly as a limitation: the model
partly learns which tests were run rather than purely physiological
patterns.
"""
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

FEATURE_COLUMNS = [
    "age", "sex_code", "location_code", "visit_month", "visit_season_code",
    "glucose", "bmi", "hba1c", "malaria_parasite_grade",
]
TARGET_COLUMN = "diagnosis"
SEED = 42


def _prepare_features(df):
    X = df[FEATURE_COLUMNS].fillna(-1)
    y = df[TARGET_COLUMN]
    return X, y


def train(train_df):
    X_train, y_train = _prepare_features(train_df)
    model = RandomForestClassifier(
        n_estimators=300, max_depth=None, class_weight="balanced",
        random_state=SEED, n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, df, tag="test"):
    X, y_true = _prepare_features(df)
    y_pred = model.predict(X)

    results = {
        "accuracy": accuracy_score(y_true, y_pred),
        "f1_macro": f1_score(y_true, y_pred, average="macro"),
        "f1_weighted": f1_score(y_true, y_pred, average="weighted"),
    }
    print(f"--- Classification results ({tag}) ---")
    for k, v in results.items():
        print(f"{k:>15s}: {v:.4f}")
    print("\n", classification_report(y_true, y_pred))
    print("Confusion matrix (rows=true, cols=pred):")
    labels = sorted(y_true.unique())
    print(pd.DataFrame(confusion_matrix(y_true, y_pred, labels=labels), index=labels, columns=labels))
    return results, y_pred


def run():
    train_df = pd.read_csv(os.path.join(PROCESSED_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(PROCESSED_DIR, "val.csv"))
    test_df = pd.read_csv(os.path.join(PROCESSED_DIR, "test.csv"))

    model = train(train_df)
    evaluate(model, val_df, tag="validation")
    test_results, _ = evaluate(model, test_df, tag="internal test")

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "classifier_rf.joblib")
    joblib.dump(model, model_path)
    print(f"Saved model to {model_path}")
    return model, test_results


if __name__ == "__main__":
    run()
