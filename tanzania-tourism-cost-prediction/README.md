# Predictive Analytics for Tanzania Tourism Costs

> Leveraging Gradient Boosting to Optimize Travel Budgeting and Pricing Strategies

## Project Overview

This project builds an end-to-end machine learning pipeline to predict the total cost of tourist trips in Tanzania. Using a dataset of 4,809 tourist records with 23 features (country of origin, age group, tour arrangement, activity type, and more), the best model — **XGBoost** — achieves **R² = 0.47** and **RMSE = 0.137** on normalized data.

**Key finding:** Tour arrangement type (package vs. independent) is by far the strongest predictor of trip cost (~46% combined feature importance), outweighing demographic factors such as age, gender, and country of origin.

---

## Project Structure

```
├── data/
│   ├── Train.csv                  # Original training data (with total_cost)
│   ├── Test.csv                   # Original test data (no total_cost)
│   ├── VariableDefinitions.csv    # Feature descriptions
│   ├── filtered_train.csv         # Cleaned training data (after EDA)
│   └── NaN_clean_test.csv         # Cleaned test data
│
├── models/
│   ├── scaler_features.pkl        # MinMaxScaler fitted on numeric features
│   ├── scaler_target.pkl          # MinMaxScaler fitted on total_cost
│   ├── encoder.pkl                # OneHotEncoder fitted on categorical features
│   └── best_xgb_model.pkl         # Best XGBoost model
│
├── notebooks/
│   ├── 1_EDA_analysis.ipynb       # Exploratory Data Analysis
│   ├── 2_EDA_test_cleaning.ipynb  #Cleaning of test data
│   ├── 3_Feature_Engineering_Modeling.ipynb    # Feature Engineering,  Modeling & Final predictions
│
├── data/
│   └── submission.csv             # Final predictions for Kaggle
│
├── requirements.txt
└── README.md
```

---

## Results

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Baseline (mean) | 0.185 | 0.128 | -0.001 |
| Linear Regression | 0.141 | 0.087 | 0.417 |
| Decision Tree | 0.143 | 0.083 | -0.075 |
| Random Forest | 0.137 | 0.079 | 0.451 |
| KNN | 0.140 | 0.081 | 0.426 |
| Gradient Boosting | 0.137 | 0.079 | 0.465 |
| **XGBoost** | **0.137** | **0.078** | **0.465** |

> All metrics computed on normalized data (MinMaxScaler, range [0, 1]).

**Best XGBoost parameters** (found via GridSearchCV, cv=3):
```
learning_rate=0.01, n_estimators=500, max_depth=5,
subsample=0.6, colsample_bytree=0.8, min_child_weight=10, gamma=0.1
```

---

## Top 10 Most Important Features

| Feature | Importance |
|---|---|
| Tour type: Package Tour | 25.4% |
| Tour type: Independent | 21.0% |
| No accommodation package | 7.8% |
| Travelling alone | 3.5% |
| Accommodation included | 2.4% |
| No international transport | 2.1% |
| International transport included | 1.9% |
| No local transport package | 1.7% |
| Group size (total people) | 1.7% |
| Food included | 1.3% |

---

## Set up your Environment

### **`macOS`**

- Using Makefile:
    ```bash
    make setup
    source .venv/bin/activate
    ```

- Manually:
    ```bash
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

### **`WindowsOS`**

For `PowerShell`:
```powershell
pyenv local 3.11.3
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For `Git-bash`:
```bash
pyenv local 3.11.3
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> **Note:** If `pip install --upgrade pip` fails on Windows, try:
> ```bash
> python.exe -m pip install --upgrade pip
> ```

---

## Usage

**1. Run EDA and preprocessing:**
Open and run `notebooks/1_EDA_analysis.ipynb`

**2. Train models, generate submission and final predictions:**
Open and run `notebooks/3_Feature_Engineering_Modeling.ipynb`


The final submission file will be saved to `data/submission.csv`.

---

## Limitations

- **R² = 0.47** — the model explains ~47% of variance in trip costs. High-spending tourists (>5,000 EUR) are systematically underestimated due to skewed target distribution.
- **No seasonality** — travel dates are not included in the dataset; peak vs. off-peak pricing is not captured.
- Development libraries are part of the environment and are not separated from production dependencies.

---


## Dataset

Source: [Kaggle — Tanzania Tourism Prediction](https://www.kaggle.com/datasets/alfredkondoro/tanzania-tourism-prediction-zindi-africa)

Files: `Train.csv`, `Test.csv`, `VariableDefinitions.csv`

**Target variable:** `total_cost` (total trip cost in TZS)

---

*Portfolio project — Nadezhda Semenova · 2025 · [LinkedIn](https://www.linkedin.com/in/nadezhda-semenova-v/)*
