"""
Classification module (PRD Section 9.1): RandomForestClassifier predicting
the diagnosis category (diabetes / typhoid / malaria / none).

Feature note (document this in Chapter 4): clinical columns are
disease-specific (e.g. glucose is only recorded for diabetes work-ups,
widal_o/widal_h only for the Unwana malaria/typhoid cohort). Missing values
are filled with -1 so the model can split on "was this test even ordered"
as its own signal - which is clinically realistic (the clinician already
narrows down the suspected disease before ordering a disease-specific
test), not just imputation noise. This is called out explicitly as a
limitation: the model partly learns which tests were run rather than
purely physiological patterns.

widal_o/widal_h (the real Widal test O/H antigen titers) are the actual
diagnostic signal that separates a typhoid-positive from a malaria-only
patient in the source study - malaria_parasite_grade alone cannot do this,
since the typhoid-labelled group is also malaria-positive (co-infected) and
so has its own non-null parasite grade.

Hyperparameters (n_estimators=500, max_depth=10, min_samples_leaf=1) were
selected by comparing validation accuracy across a small grid (see the
project history/commit message for the grid), not hand-picked to hit a
target number. Per standard practice once hyperparameters are chosen, the
reported final model is refit on train+validation combined and evaluated
only on the still-untouched test set (run() below does this explicitly -
evaluate_validation_only() exists separately so the validation-stage check
used during development remains reproducible).
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
    "glucose", "bmi", "hba1c", "blood_pressure_systolic", "family_history", "hypertension",
    "malaria_parasite_grade", "widal_o", "widal_h",
]
TARGET_COLUMN = "diagnosis"
SEED = 42


def _prepare_features(df):
    X = df[FEATURE_COLUMNS].fillna(-1)
    y = df[TARGET_COLUMN]
    return X, y


def train(df):
    X, y = _prepare_features(df)
    model = RandomForestClassifier(
        n_estimators=500, max_depth=10, min_samples_leaf=1, class_weight="balanced",
        random_state=SEED, n_jobs=-1,
    )
    model.fit(X, y)
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

    # Stage 1: train-only model, for the validation-stage diagnostic check.
    val_stage_model = train(train_df)
    evaluate(val_stage_model, val_df, tag="validation (train-only model)")

    # Stage 2: once hyperparameters are chosen, refit on train+validation
    # combined for the reported final model - test stays untouched throughout.
    trainval_df = pd.concat([train_df, val_df], ignore_index=True)
    model = train(trainval_df)
    test_results, _ = evaluate(model, test_df, tag="internal test (final model, trained on train+val)")

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "classifier_rf.joblib")
    joblib.dump(model, model_path)
    print(f"Saved model to {model_path}")
    return model, test_results


if __name__ == "__main__":
    run()
