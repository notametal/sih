"""
Trains a tiny decision tree on drying-sensor data and exports it as a
plain C function that can be compiled directly into Arduino firmware.
No TFLite Micro, no interpreter, no model blob — just nested if/else
on floats. Fits comfortably in an Uno R3's 2KB RAM / 32KB flash.

Usage:
    python3 train_tree.py sample_data.csv model_tree.h

CSV must have columns:
    temperature, humidity, humidity_change, temperature_change,
    elapsed_time, label
"""

import sys
import csv
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix

FEATURES = [
    "temperature",
    "humidity",
    "humidity_change",
    "temperature_change",
    "elapsed_time",
]

def load_csv(path):
    X, y = [], []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in FEATURES + ["label"] if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}")
        for row in reader:
            X.append([float(row[c]) for c in FEATURES])
            y.append(int(row["label"]))
    return X, y


def tree_to_c(tree, feature_names, func_name="dryingCompletePredict"):
    t = tree.tree_
    lines = []
    lines.append("// Auto-generated from a trained sklearn DecisionTreeClassifier.")
    lines.append("// Do not hand-edit — regenerate with train_tree.py instead.")
    lines.append(f"int {func_name}(float temperature, float humidity, "
                  "float humidity_change, float temperature_change, "
                  "float elapsed_time) {")

    def recurse(node, depth):
        indent = "  " * (depth + 1)
        if t.feature[node] != -2:
            fname = feature_names[t.feature[node]]
            threshold = t.threshold[node]
            lines.append(f"{indent}if ({fname} <= {threshold:.4f}f) {{")
            recurse(t.children_left[node], depth + 1)
            lines.append(f"{indent}}} else {{")
            recurse(t.children_right[node], depth + 1)
            lines.append(f"{indent}}}")
        else:
            counts = t.value[node][0]
            predicted_class = int(counts.argmax())
            lines.append(f"{indent}return {predicted_class};  "
                          f"// leaf, class counts: {counts.tolist()}")

    recurse(0, 0)
    lines.append("}")
    return "\n".join(lines)


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "sample_data.csv"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "model_tree.h"
    max_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    X, y = load_csv(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_leaf=10,
        random_state=42,
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    cm = confusion_matrix(y_test, preds)

    print(f"Trained on {len(X_train)} rows, tested on {len(X_test)} rows")
    print(f"Test accuracy: {acc:.4f}")
    print(f"Confusion matrix [[TN FP] [FN TP]]:\n{cm}")
    print(f"Tree depth: {clf.get_depth()}, leaves: {clf.get_n_leaves()}")

    c_code = tree_to_c(clf, FEATURES)

    header = f"""#ifndef DRYING_MODEL_TREE_H
#define DRYING_MODEL_TREE_H

// Trained on: {csv_path}
// Test accuracy: {acc:.4f}
// Tree depth: {clf.get_depth()}  |  Leaves: {clf.get_n_leaves()}

{c_code}

#endif // DRYING_MODEL_TREE_H
"""

    with open(out_path, "w") as f:
        f.write(header)

    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
