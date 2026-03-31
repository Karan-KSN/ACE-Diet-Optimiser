import streamlit as st
import pandas as pd

# --- 1. SET UP THE NIN CSV DATABASE ---
@st.cache_data
def load_data():
    df = pd.read_csv('ifct2017_compositions.csv')
    df = df[['name', 'protcnt', 'choavldf', 'fatce', 'na', 'k']]
    df.columns = ['Food Item', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg']
    
    numeric_cols = ['Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

# Initialize the state tracker for macros and micros
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'])

# --- 2. BUILD THE USER INTERFACE ---
st.title("🧬 Nutrigenetic Meal Optimizer")
st.markdown("Automated IFCT pipeline for North Indian dietary tracking.")

# Genotype Selector
st.sidebar.header("Patient Genetic Profile")
genotype = st.sidebar.radio(
    "Select ACE I/D Genotype:",
    ("II / ID (Standard Risk)", "DD (High Risk - Sodium Sensitive)")
)

# --- 3. APPLY THE BIOINFORMATICS RULES ---
if genotype == "DD (High Risk - Sodium Sensitive)":
    max_sodium = 1500
    target_potassium = 3500
else:
    max_sodium = 2300
    target_potassium = 2500

st.sidebar.markdown("### Daily Thresholds")
st.sidebar.write(f"🛑 **Max Sodium:** {max_sodium} mg")
st.sidebar.write(f"✅ **Target Potassium:** {target_potassium} mg")

# --- 4. FOOD SELECTION LOGIC ---
st.subheader("Add Food to Daily Intake")
col1, col2 = st.columns([3, 1])

with col1:
    selected_food = st.selectbox("Search Indian Food Database:", df['Food Item'])
with col2:
    if st.button("Add to Meal"):
        food_data = df[df['Food Item'] == selected_food].iloc[0]
        st.session_state.meal_plan.loc[len(st.session_state.meal_plan)] = food_data

# --- 5. CALCULATE TOTALS & RENDER UI ---
current_sodium = st.session_state.meal_plan['Sodium_mg'].sum() if not st.session_state.meal_plan.empty else 0
current_potassium = st.session_state.meal_plan['Potassium_mg'].sum() if not st.session_state.meal_plan.empty else 0
current_protein = st.session_state.meal_plan['Protein_g'].sum() if not st.session_state.meal_plan.empty else 0
current_carbs = st.session_state.meal_plan['Carbs_g'].sum() if not st.session_state.meal_plan.empty else 0
current_fats = st.session_state.meal_plan['Fat_g'].sum() if not st.session_state.meal_plan.empty else 0

st.divider()
st.subheader("Live Biomarker & Macro Tracking")

# Macro Tracker
st.write(f"💪 **Macros Consumed:** Protein: {current_protein:.1f}g | Carbs: {current_carbs:.1f}g | Fats: {current_fats:.1f}g")
st.markdown("---")

# Sodium Tracking
st.write(f"**Sodium:** {current_sodium:.1f} mg / {max_sodium} mg")
sodium_percent = min(current_sodium / max_sodium, 1.0)
if current_sodium > max_sodium:
    st.error("⚠️ GENETIC LIMIT EXCEEDED: Vasoconstriction risk elevated.")
st.progress(sodium_percent)

# Potassium Tracking
st.write(f"**Potassium:** {current_potassium:.1f} mg / {target_potassium} mg")
potassium_percent = min(current_potassium / target_potassium, 1.0)
if current_potassium >= target_potassium:
    st.success("🎯 TARGET REACHED: Optimal vasodilation support.")
st.progress(potassium_percent)

# --- 6. DISPLAY CURRENT MEAL PLAN ---
st.subheader("Current Meal Plan")
if not st.session_state.meal_plan.empty:
    st.dataframe(st.session_state.meal_plan)
    if st.button("Clear Meal Plan"):
        st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'])
        st.rerun()
else:
    st.info("No foods added yet.")
