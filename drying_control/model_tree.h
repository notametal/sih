#ifndef DRYING_MODEL_TREE_H
#define DRYING_MODEL_TREE_H

// Trained on: sample_data.csv
// Test accuracy: 1.0000
// Tree depth: 1  |  Leaves: 2

// Auto-generated from a trained sklearn DecisionTreeClassifier.
// Do not hand-edit — regenerate with train_tree.py instead.
int dryingCompletePredict(float temperature, float humidity, float humidity_change, float temperature_change, float elapsed_time) {
  if (humidity <= 24.0900f) {
    return 1;  // leaf, class counts: [0.4, 0.6]
  } else {
    return 0;  // leaf, class counts: [1.0, 0.0]
  }
}

#endif // DRYING_MODEL_TREE_H
