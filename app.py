import streamlit as st
import pandas as pd

# --- 1. SET UP THE NIN CSV DATABASE ---
@st.cache_data
def load_data():
    df = pd.read_csv('ifct2017_compositions.csv')
    # Added 'enerc' to fetch Energy (Calories)
    df = df[['name', 'protcnt', 'choavldf', 'fatce', 'na', 'k', 'enerc']]
    df.columns = ['Food Item', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal']
    
    numeric_cols = ['Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=[
        'Food Item', 'Portion', 'Energy_kcal', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'
    ])

# --- 2. BUILD THE UI ---
st.set_page_config(page_title="Nutrigenetic CDSS", layout="centered")
st.title("🧬 Nutrigenetic Clinical Optimizer")
st.markdown("Automated IFCT tracking with metabolic and GxE interaction rules.")

# --- 3. PATIENT DEMOGRAPHICS & ANTHROPOMETRY ---
st.header("1. Demographics & Energy Expenditure")
col_age, col_gen = st.columns(2)
age = col_age.number_input("Age (Years)", min_value=1, max_value=120, value=45)
gender = col_gen.selectbox("Gender", ["Male", "Female"])

col_h, col_w = st.columns(2)
height_cm = col_h.number_input("Height (cm)", min_value=50.0, max_value=300.0, value=170.0)
weight_kg = col_w.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0)

activity_level = st.selectbox("Physical Activity Level (PAL):", [
    "Sedentary (Little or no exercise)",
    "Lightly Active (Exercise 1-3 days/week)",
    "Moderately Active (Exercise 3-5 days/week)",
    "Very Active (Hard exercise 6-7 days/week)",
    "Extra Active (Physical job or training twice a day)"
])

# Auto-calculate BMI
height_m = height_cm / 100.0
bmi = weight_kg / (height_m ** 2) if height_m > 0 else 0

if bmi < 18.5: bmi_status = "Underweight"
elif 18.5 <= bmi <= 22.9: bmi_status = "Normal (Asian Standard)"
elif 23.0 <= bmi <= 24.9: bmi_status = "Overweight"
else: bmi_status = "Obese"

# Mifflin-St Jeor Equation for BMR
if gender == "Male":
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
else:
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161

# Apply Activity Multiplier
activity_multipliers = {
    "Sedentary (Little or no exercise)": 1.2,
    "Lightly Active (Exercise 1-3 days/week)": 1.375,
    "Moderately Active (Exercise 3-5 days/week)": 1.55,
    "Very Active (Hard exercise 6-7 days/week)": 1.725,
    "Extra Active (Physical job or training twice a day)": 1.9
}
tdee = bmr * activity_multipliers[activity_level]

# Auto-Calculate Daily Requirements
# Water: 35ml per kg of bodyweight
water_req_liters = (weight_kg * 35) / 1000 
# AMDR Splits: 20% Protein, 55% Carbs, 25% Fats
target_protein = (tdee * 0.20) / 4   # 4 kcal per gram of protein
target_carbs = (tdee * 0.55) / 4     # 4 kcal per gram of carbs
target_fat = (tdee * 0.25) / 9       # 9 kcal per gram of fat

st.info(f"""
⚖️ **BMI:** {bmi:.1f} kg/m² ({bmi_status})
🔥 **BMR:** {bmr:.0f} kcal/day | **TDEE (Daily Caloric Need):** {tdee:.0f} kcal
💧 **Daily Hydration Target:** {water_req_liters:.1f} Liters
""")
st.divider()

# --- 4. GENETIC PROFILE & METABOLIC WINDOWS ---
st.header("2. Genetic Profile & Prescribed Windows")
genotype = st.radio("Select ACE I/D Genotype:", ("II / ID (Standard Risk)", "DD (High Risk - Sodium Sensitive)"), horizontal=True)

max_sodium = 1500 if "DD" in genotype else 2300
target_potassium = 3500 if "DD" in genotype else 2500

st.write(f"🔬 **Micro Windows:** Max Sodium = {max_sodium} mg | Target Potassium = {target_potassium} mg")
st.write(f"📊 **Auto-Calculated Macros (IOM AMDR):** Protein: {target_protein:.0f}g | Carbs: {target_carbs:.0f}g | Fats: {target_fat:.0f}g")
st.divider()

# --- 5. FOOD SELECTION LOGIC ---
st.header("3. Add Food Intake")
portions = {
    "Grams (Custom Entry)": 100,
    "1 Katori / Small Bowl (~150g)": 150,
    "1 Medium Cup (~250g)": 250,
    "1 Tablespoon (~15g)": 15,
    "1 Standard Piece/Roti (~40g)": 40
}

selected_food = st.selectbox("Search Indian Food Database (IFCT):", df['Food Item'])
col1, col2 = st.columns(2)
with col1:
    portion_type = st.selectbox("Select Portion Unit:", list(portions.keys()))
with col2:
    if portion_type == "Grams (Custom Entry)":
        grams_input = st.number_input("Enter exact Grams:", min_value=1, value=100)
    else:
        grams_input = portions[portion_type]
        st.number_input("Equivalent Grams:", value=grams_input, disabled=True)

if st.button("➕ Add to Intake Window", use_container_width=True):
    base_data = df[df['Food Item'] == selected_food].iloc[0]
    multiplier = grams_input / 100.0
    new_row = pd.DataFrame([{
        'Food Item': selected_food,
        'Portion': f"{grams_input}g",
        'Energy_kcal': round(base_data['Energy_kcal'] * multiplier, 1),
        'Sodium_mg': round(base_data['Sodium_mg'] * multiplier, 1),
        'Potassium_mg': round(base_data['Potassium_mg'] * multiplier, 1),
        'Protein_g': round(base_data['Protein_g'] * multiplier, 1),
        'Carbs_g': round(base_data['Carbs_g'] * multiplier, 1),
        'Fat_g': round(base_data['Fat_g'] * multiplier, 1)
    }])
    st.session_state.meal_plan = pd.concat([st.session_state.meal_plan, new_row], ignore_index=True)

st.divider()

# --- 6. LIVE METABOLIC TRACKING ---
curr_kcal = st.session_state.meal_plan['Energy_kcal'].sum() if not st.session_state.meal_plan.empty else 0
curr_pro = st.session_state.meal_plan['Protein_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_carb = st.session_state.meal_plan['Carbs_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_fat = st.session_state.meal_plan['Fat_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_na = st.session_state.meal_plan['Sodium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_k = st.session_state.meal_plan['Potassium_mg'].sum() if not st.session_state.meal_plan.empty else 0

st.header("4. Live Metabolic Tracking")

st.subheader("Energy & Macronutrient Windows")
st.write(f"⚡ **Calories:** {curr_kcal:.0f} kcal Consumed | **{max(0, tdee - curr_kcal):.0f} kcal Left**")
st.progress(min(curr_kcal / tdee, 1.0) if tdee > 0 else 0)

st.write(f"🥩 **Protein:** {curr_pro:.1f}g Consumed | **{max(0, target_protein - curr_pro):.1f}g Left**")
st.progress(min(curr_pro / target_protein, 1.0) if target_protein > 0 else 0)

st.write(f"🍚 **Carbs:** {curr_carb:.1f}g Consumed | **{max(0, target_carbs - curr_carb):.1f}g Left**")
st.progress(min(curr_carb / target_carbs, 1.0) if target_carbs > 0 else 0)

st.write(f"🧈 **Fats:** {curr_fat:.1f}g Consumed | **{max(0, target_fat - curr_fat):.1f}g Left**")
st.progress(min(curr_fat / target_fat, 1.0) if target_fat > 0 else 0)

st.markdown("---")
st.subheader("Genetic Micronutrient Windows (RAAS)")

st.write(f"🧂 **Sodium:** {curr_na:.1f} mg Consumed | **{max(0, max_sodium - curr_na):.1f} mg Left**")
if curr_na > max_sodium: st.error(f"⚠️ GENETIC LIMIT EXCEEDED BY {round(curr_na - max_sodium, 1)} mg")
st.progress(min(curr_na / max_sodium, 1.0))

st.write(f"🍌 **Potassium:** {curr_k:.1f} mg Consumed | **Target: {target_potassium} mg**")
if curr_k >= target_potassium: st.success("🎯 TARGET REACHED: Optimal vasodilation support.")
st.progress(min(curr_k / target_potassium, 1.0))

# --- 7. SCIENTIFIC JUSTIFICATION ---
with st.expander("📚 Scientific Literature & Equations Used"):
    st.markdown("""
    **Equations & Guidelines:**
    * **BMR/TDEE:** Mifflin-St Jeor Equation (Mifflin et al., 1990, *Am J Clin Nutr*). Validated as the most reliable predictor of REE in non-clinical and clinical populations.
    * **Macronutrient Split:** AMDR guidelines (Institute of Medicine, 2005) customized to 20% Protein, 55% Carbs, 25% Fats for balanced baseline metabolic support.
    * **Hydration:** Standard physiological baseline of 35ml per kg of body weight.
    
    **Genetics (ACE I/D):**
    * **Srivastava et al. (2012)**: *Assoc. of ACE Gene Polymorphism with Essential Hypertension in North Indian Population.*
    * **Poch et al. (2001)**: Confirmed the interaction between ACE variants and sodium limits.
    """)

# --- 8. CURRENT INTAKE LOG ---
st.subheader("Current Intake Log")
if not st.session_state.meal_plan.empty:
    st.dataframe(st.session_state.meal_plan, use_container_width=True)
    if st.button("Clear Log"):
        st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Portion', 'Energy_kcal', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'])
        st.rerun()
