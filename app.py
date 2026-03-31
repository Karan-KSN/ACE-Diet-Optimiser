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

# Initialize the state tracker
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=[
        'Food Item', 'Portion', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'
    ])

# --- 2. BUILD THE MOBILE-FRIENDLY UI ---
st.set_page_config(page_title="Nutrigenetic Optimizer", layout="centered")
st.title("🧬 Nutrigenetic Meal Optimizer")

# Moved Genetic Profile out of the sidebar into the main screen
st.header("1. Metabolic & Genetic Windows")
genotype = st.radio(
    "Select ACE I/D Genotype:",
    ("II / ID (Standard Risk)", "DD (High Risk - Sodium Sensitive)"),
    horizontal=True
)

if "DD" in genotype:
    max_sodium = 1500
    target_potassium = 3500
else:
    max_sodium = 2300
    target_potassium = 2500

st.info(f"🔬 **Micro Windows:** Max Sodium = {max_sodium} mg | Target Potassium = {target_potassium} mg")

# Macro Target Inputs
st.markdown("**Set Daily Macro Targets:**")
col_p, col_c, col_f = st.columns(3)
target_protein = col_p.number_input("Protein (g)", value=120)
target_carbs = col_c.number_input("Carbs (g)", value=250)
target_fat = col_f.number_input("Fats (g)", value=60)

st.divider()

# --- 3. FOOD & QUANTITY SELECTION LOGIC ---
st.header("2. Add Food Intake")

# Define standard portion sizes in grams for the mathematical multiplier
portions = {
    "Grams (Custom Entry)": 100,
    "1 Katori / Small Bowl (~150g)": 150,
    "1 Medium Cup (~250g)": 250,
    "1 Tablespoon (~15g)": 15,
    "1 Standard Piece/Roti (~40g)": 40
}

selected_food = st.selectbox("Search Indian Food Database (IFCT Base: 100g):", df['Food Item'])

col1, col2 = st.columns(2)
with col1:
    portion_type = st.selectbox("Select Portion Unit:", list(portions.keys()))
with col2:
    if portion_type == "Grams (Custom Entry)":
        grams_input = st.number_input("Enter exact Grams:", min_value=1, value=100)
    else:
        grams_input = portions[portion_type]
        st.number_input("Equivalent Grams (Auto-calculated):", value=grams_input, disabled=True)

if st.button("➕ Add to Intake Window", use_container_width=True):
    # Fetch base 100g values
    base_data = df[df['Food Item'] == selected_food].iloc[0]
    
    # Calculate IFCT multiplier
    multiplier = grams_input / 100.0
    
    # Create new row with adjusted, multiplier-applied values
    new_row = pd.DataFrame([{
        'Food Item': selected_food,
        'Portion': f"{grams_input}g",
        'Sodium_mg': round(base_data['Sodium_mg'] * multiplier, 1),
        'Potassium_mg': round(base_data['Potassium_mg'] * multiplier, 1),
        'Protein_g': round(base_data['Protein_g'] * multiplier, 1),
        'Carbs_g': round(base_data['Carbs_g'] * multiplier, 1),
        'Fat_g': round(base_data['Fat_g'] * multiplier, 1)
    }])
    st.session_state.meal_plan = pd.concat([st.session_state.meal_plan, new_row], ignore_index=True)

st.divider()

# --- 4. CALCULATE TOTALS & RENDER PROGRESS ---
current_sodium = st.session_state.meal_plan['Sodium_mg'].sum() if not st.session_state.meal_plan.empty else 0
current_potassium = st.session_state.meal_plan['Potassium_mg'].sum() if not st.session_state.meal_plan.empty else 0
current_protein = st.session_state.meal_plan['Protein_g'].sum() if not st.session_state.meal_plan.empty else 0
current_carbs = st.session_state.meal_plan['Carbs_g'].sum() if not st.session_state.meal_plan.empty else 0
current_fats = st.session_state.meal_plan['Fat_g'].sum() if not st.session_state.meal_plan.empty else 0

st.header("3. Live Metabolic Tracking")

# Macro Windows (Consumed vs Left)
st.subheader("Macronutrient Windows")
st.write(f"🥩 **Protein:** {current_protein:.1f}g Consumed | **{max(0, target_protein - current_protein):.1f}g Left**")
st.progress(min(current_protein / target_protein, 1.0))

st.write(f"🍚 **Carbs:** {current_carbs:.1f}g Consumed | **{max(0, target_carbs - current_carbs):.1f}g Left**")
st.progress(min(current_carbs / target_carbs, 1.0))

st.write(f"🧈 **Fats:** {current_fats:.1f}g Consumed | **{max(0, target_fat - current_fats):.1f}g Left**")
st.progress(min(current_fats / target_fat, 1.0))

st.markdown("---")

# Micro Windows (Sodium & Potassium)
st.subheader("Genetic Micronutrient Windows (RAAS)")

st.write(f"🧂 **Sodium:** {current_sodium:.1f} mg Consumed | **{max(0, max_sodium - current_sodium):.1f} mg Left**")
if current_sodium > max_sodium:
    st.error(f"⚠️ GENETIC LIMIT EXCEEDED BY {round(current_sodium - max_sodium, 1)} mg: Vasoconstriction risk elevated.")
st.progress(min(current_sodium / max_sodium, 1.0))

st.write(f"🍌 **Potassium:** {current_potassium:.1f} mg Consumed | **Target: {target_potassium} mg**")
if current_potassium >= target_potassium:
    st.success("🎯 TARGET REACHED: Optimal vasodilation support.")
st.progress(min(current_potassium / target_potassium, 1.0))

# --- 5. DISPLAY CURRENT INTAKE LOG ---
st.subheader("Current Intake Log")
if not st.session_state.meal_plan.empty:
    st.dataframe(st.session_state.meal_plan, use_container_width=True)
    if st.button("Clear Log"):
        st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Portion', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'])
        st.rerun()
else:
    st.info("No foods added to the window yet.")
