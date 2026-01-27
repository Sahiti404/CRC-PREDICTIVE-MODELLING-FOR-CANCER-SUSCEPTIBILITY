from fastapi import FastAPI
from pydantic import BaseModel



import math
import numpy as np
import pandas as pd

app = FastAPI()

class PatientInput(BaseModel):
    age: float
    bmi: float
    gender: str
    kras: int
    apc: int
    tp53: int
    mmr: int

# =========================================================
# PART 1: PATERSON MODEL CONSTANTS (FROM PATERSON et al.)
# =========================================================

# Number of colorectal crypts
N = 1e8

# Base mutation rate (per base per year)
u = 1.25e-8

# Driver gene target sizes
n_APC = 604
n_TP53 = 73
n_KRAS = 20

# Gene-specific mutation rates
r_APC = n_APC * u
r_TP53 = n_TP53 * u
r_KRAS = n_KRAS * u

# Loss of heterozygosity rate
r_LOH = 1.36e-4

# Crypt growth advantages
b1 = 0.20   # APC−/−
b2 = 0.07   # KRAS+
b12 = b1 + b2

# Fixation correction constants
c1 = 5.88
c2 = 3.6
c = c1 * c2

# =========================================================
# PART 2: BASELINE HAZARD & PATERSON RISK
# =========================================================

def baseline_hazard(age):
    """
    Baseline cumulative hazard H0(t) for CRC initiation
    using Paterson APC+KRAS shape:
        H0(t) ≈ A * t^2 * exp(b12 * t)
    """
    A = (
        c * N * r_APC * r_TP53 * r_KRAS * (r_LOH ** 2)
        * (
            1 / (b12**3 * (b12 - b1)) +
            1 / (b12**3 * (b12 - b2)) +
            1 / (b12**2 * (b12 - b2)**2)
        )
    )
    H0 = A * (age ** 2) * math.exp(b12 * age)

    # Cap to avoid numerical overflow in exp(-H0)
    if H0 > 50:
        H0 = 50.0
    return H0

def paterson_baseline_risk(age):
    """
    Baseline cumulative CRC risk by age:
        P0(t) = 1 - exp(-H0(t))
    """
    H0 = baseline_hazard(age)
    return 1 - math.exp(-H0)

# =========================================================
# PART 3: LOAD ML COEFFICIENTS (INTERPRETABLE MODEL)
# =========================================================

coeff = pd.read_csv(
    "ML_coefficients_step4_with_gender.csv",
    index_col=0
).iloc[:, 0]

# Literature-guided clinical scaling (relative effect strength)
clinical_scale = {
    "TP53_mut": 0.5,      # RR ~ 1.5–2.0
    "APC_mut": 1.0,       # RR ~ 10–100
    "MMR_defect": 1.0,    # RR ~ 2–8
    "KRAS_mut": 0.3,      # RR ~ 1.2–1.5
    "BMI": 0.2,           # RR ~ 1.2–1.5
    "Sex_bin": 0.1        # RR ~ 1.4
}

def compute_alpha(patient_features, log_alpha_base):
    """
    Hybrid personalization:
    - Relative importance from ML
    - Absolute scaling from biological literature
    """
    # Normalize by APC mutation coefficient (reference)
    ref_coef = coeff["APC_mut"]
    norm_coeff = coeff.abs() / ref_coef

    log_alpha = log_alpha_base

    for feature, value in patient_features.items():
        if feature in norm_coeff.index:
            if feature == "BMI":
                if value > 25:
                    log_alpha += min(clinical_scale[feature] * norm_coeff[feature] * (value - 25), 1.0)
            elif feature == "Sex_bin":
                if value == 0:   # female
                    log_alpha -= min(clinical_scale[feature] * norm_coeff[feature], 0.3)
            else:
                log_alpha += min(clinical_scale[feature] * norm_coeff[feature] * value, 1.0)

    # Set minimum and maximum for α to prevent extreme values
    alpha = math.exp(log_alpha)
    return max(min(alpha, 5.0), 0.01)

# =========================================================
# PART 4: PERSONALIZED & CONDITIONAL RISK
# =========================================================

def personalized_risk(age, alpha):
    """
    Personalized cumulative risk:
        H(t) = α * H0(t)
        P(t) = 1 - exp(-H(t))
    """
    H0 = baseline_hazard(age)
    H = alpha * H0
    if H > 50:
        H = 50.0
    return 1 - math.exp(-H)

def conditional_risk(age_now, age_future, alpha):
    """
    Conditional probability of CRC initiation between age_now and age_future
    given survival (no CRC) up to age_now.
    """
    p_now = personalized_risk(age_now, alpha)
    p_future = personalized_risk(age_future, alpha)
    if p_now >= 1.0:
        return 0.0
    return (p_future - p_now) / (1 - p_now)

# =========================================================
# PART 5: LOAD SEER DATA (2018–2023)
# =========================================================

seer_df = pd.read_csv("SEER_formatted_for_calibration.csv")

def get_seer_incidence(age, sex_bin):
    """
    Returns SEER annual incidence rate per 100,000
    for the matching age band and sex.
    sex_bin: 0 = female, 1 = male
    """
    for _, row in seer_df.iterrows():
        start, end = map(int, row["Age_Group"].split("-"))
        if start <= age <= end:
            return row["Male_Rate"] if sex_bin == 1 else row["Female_Rate"]
    raise ValueError("Age not covered in SEER table")

def calibrate_log_alpha(age, sex_bin):
    """
    Calibrate baseline hazard so that 5-year model risk
    matches SEER short-term incidence (population average)
    at the given age and sex.
    """
    incidence = get_seer_incidence(age, sex_bin)
    target_5yr = 1 - math.exp(-5 * incidence / 100000)

    # Use bisection for robust calibration
    low, high = -5, 2
    for _ in range(100):
        mid = (low + high) / 2
        alpha = math.exp(mid)
        model_5yr = conditional_risk(age, age + 5, alpha)
        if abs(model_5yr - target_5yr) < 1e-4:
            return mid
        elif model_5yr < target_5yr:
            low = mid
        else:
            high = mid
    return mid

# =========================================================
# PART 6: CALIBRATION DEBUG CHECK
# =========================================================

def debug_check_calibration():
    """
    Print SEER vs model 5-year risk for a few ages and both sexes.
    Helps verify that calibration works at the population level.
    """
    test_ages = [45, 50, 60, 70]
    for sex_bin in [0, 1]:   # 0 = female, 1 = male
        sex_label = "Female" if sex_bin == 0 else "Male"
        print(f"\n=== Calibration check for {sex_label} ===")
        for age in test_ages:
            incidence = get_seer_incidence(age, sex_bin)
            target_5yr = 1 - math.exp(-5 * incidence / 100000)
            log_alpha = calibrate_log_alpha(age, sex_bin)
            alpha = math.exp(log_alpha)
            model_5yr = conditional_risk(age, age + 5, alpha)
            print(
                f"Age {age}: SEER 5-yr = {target_5yr*100:.3f}% , "
                f"Model 5-yr = {model_5yr*100:.3f}% , "
                f"log_alpha = {log_alpha:.3f}"
            )

# =========================================================
# PART 7: MODERN POPULATION BASELINE (RELATIVE COMPARISON)
# =========================================================

def population_lifetime_risk(sex_bin):
    """
    Modern SEER / NCI / ACS trend-adjusted lifetime CRC risk.
    Used ONLY for relative population comparison.
    """
    return 0.043 if sex_bin == 1 else 0.040

def relative_risk_category(rr):
    if rr < 1.0:
        return "Below average population risk"
    elif rr < 2.0:
        return "Average population risk"
    elif rr < 4.0:
        return "Moderately elevated risk"
    else:
        return "Very high risk"

# =========================================================
# PART 8: MAIN – DEBUG CALIBRATION + USER INPUT
# =========================================================

# Calibration check (you can comment this out later if it is too verbose)
print("\n### DEBUG: Calibration vs SEER ###")
debug_check_calibration()

@app.post("/predict")
def predict_risk(data: PatientInput):
    sex_bin = 1 if data.gender.lower() == "male" else 0

    patient = {
        "BMI": data.bmi,
        "Sex_bin": sex_bin,
        "KRAS_mut": data.kras,
        "TP53_mut": data.tp53,
        "APC_mut": data.apc,
        "MMR_defect": data.mmr
    }

    log_alpha = calibrate_log_alpha(data.age, sex_bin)
    alpha = compute_alpha(patient, log_alpha)

    risk_5yr = conditional_risk(data.age, data.age + 5, alpha)
    risk_10yr = conditional_risk(data.age, data.age + 10, alpha)
    lifetime_risk = personalized_risk(80, alpha)

    risk_5yr = conditional_risk(data.age, data.age + 5, alpha)
    risk_10yr = conditional_risk(data.age, data.age + 10, alpha)


    return {
        "risk_5yr_percent": round(risk_5yr * 100, 2),
        "risk_10yr_percent": round(risk_10yr * 100, 2),
        "alpha": round(alpha, 3)
    }




