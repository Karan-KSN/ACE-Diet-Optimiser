import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SET UP THE NIN CSV DATABASE (Now with Ca & Mg) ---
@st.cache_data
def load_data():
    df = pd.read_csv('ifct2017_compositions.csv')
    df = df[['name', 'protcnt', 'choavldf', 'fatce', 'na', 'k', 'enerc', 'ca', 'mg']]
    df.columns = ['Food Item', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal', 'Calcium_mg', 'Magnesium_mg']
    
    numeric_cols = ['Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal', 'Calcium_mg', 'Magnesium_mg']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

df = load_data()

if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=[
        'Food Item', 'Portion', 'Energy_kcal', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Calcium_mg', 'Magnesium_mg'
    ])

# --- 2. BUILD THE UI & TABS ---
st.set_page_config(page_title="Nutrigenetic CDSS", layout="centered")
st.title("🧬 Clinical Nutrigenetic CDSS")
st.markdown("Automated IFCT tracking, DASH Biomarkers, & ACE GxE Interactions.")

# Create Clinical Dashboard Tabs
tab1, tab2, tab3, tab4 = st.tabs(["👤 Patient Setup", "🍲 Diet & Suggestions", "📊 Visual Analytics", "📄 Reports & Lit"])

# ==========================================
# TAB 1: PATIENT DEMOGRAPHICS & GENETICS
# ==========================================
with tab1:
    st.header("Patient Demographics & Energy Setup")
    col_age, col_gen = st.columns(2)
    age = col_age.number_input("Age (Years)", min_value=1, max_value=120, value=45)
    gender = col_gen.selectbox("Gender", ["Male", "Female"])

    col_h, col_w = st.columns(2)
    height_cm = col_h.number_input("Height (cm)", min_value=50.0, max_value=300.0, value=170.0)
    weight_kg = col_w.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0)

    activity_level = st.selectbox("Physical Activity Level (PAL):", [
        "Sedentary (Little/no exercise)", "Lightly Active", "Moderately Active", "Very Active", "Extra Active"
    ])

    # BMI & TDEE Math
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2) if height_m > 0 else 0
    if bmi < 18.5: bmi_status = "Underweight"
    elif 18.5 <= bmi <= 22.9: bmi_status = "Normal (Asian Standard)"
    elif 23.0 <= bmi <= 24.9: bmi_status = "Overweight"
    else: bmi_status = "Obese"

    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + (5 if gender == "Male" else -161)
    activity_multipliers = {"Sedentary (Little/no exercise)": 1.2, "Lightly Active": 1.375, "Moderately Active": 1.55, "Very Active": 1.725, "Extra Active": 1.9}
    tdee = bmr * activity_multipliers[activity_level]

    target_protein = (tdee * 0.20) / 4   
    target_carbs = (tdee * 0.55) / 4     
    target_fat = (tdee * 0.25) / 9       

    st.info(f"⚖️ **BMI:** {bmi:.1f} ({bmi_status}) | 🔥 **TDEE:** {tdee:.0f} kcal/day")

    st.header("Genetic Profile (ACE I/D)")
    genotype = st.radio("Select ACE Genotype:", ("II / ID (Standard Risk)", "DD (High Risk - Sodium Sensitive)"), horizontal=True)
    max_sodium = 1500 if "DD" in genotype else 2300
    target_potassium = 3500 if "DD" in genotype else 2500
    # DASH Diet Constants
    target_calcium = 1000
    target_magnesium = 400

# ==========================================
# CALCULATE LIVE TOTALS (Hidden background math)
# ==========================================
curr_kcal = st.session_state.meal_plan['Energy_kcal'].sum() if not st.session_state.meal_plan.empty else 0
curr_pro = st.session_state.meal_plan['Protein_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_carb = st.session_state.meal_plan['Carbs_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_fat = st.session_state.meal_plan['Fat_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_na = st.session_state.meal_plan['Sodium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_k = st.session_state.meal_plan['Potassium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_ca = st.session_state.meal_plan['Calcium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_mg = st.session_state.meal_plan['Magnesium_mg'].sum() if not st.session_state.meal_plan.empty else 0

rem_kcal = max(0, tdee - curr_kcal)
rem_na = max(0, max_sodium - curr_na)

# ==========================================
# TAB 2: DIETARY INTAKE & SMART SUGGESTIONS
# ==========================================
with tab2:
    st.header("Log Food Intake")
    portions = {"Grams (Custom Entry)": 100, "1 Katori (~150g)": 150, "1 Medium Cup (~250g)": 250, "1 Tablespoon (~15g)": 15, "1 Roti (~40g)": 40}
    selected_food = st.selectbox("Search Indian Food Database (IFCT):", df['Food Item'])
    
    col1, col2 = st.columns(2)
    with col1:
        portion_type = st.selectbox("Select Portion Unit:", list(portions.keys()))
    with col2:
        grams_input = st.number_input("Enter exact Grams:", min_value=1, value=portions[portion_type] if portion_type != "Grams (Custom Entry)" else 100)

    if st.button("➕ Add to Window", use_container_width=True):
        base = df[df['Food Item'] == selected_food].iloc[0]
        mult = grams_input / 100.0
        new_row = pd.DataFrame([{
            'Food Item': selected_food, 'Portion': f"{grams_input}g",
            'Energy_kcal': round(base['Energy_kcal'] * mult, 1), 'Protein_g': round(base['Protein_g'] * mult, 1),
            'Carbs_g': round(base['Carbs_g'] * mult, 1), 'Fat_g': round(base['Fat_g'] * mult, 1),
            'Sodium_mg': round(base['Sodium_mg'] * mult, 1), 'Potassium_mg': round(base['Potassium_mg'] * mult, 1),
            'Calcium_mg': round(base['Calcium_mg'] * mult, 1), 'Magnesium_mg': round(base['Magnesium_mg'] * mult, 1)
        }])
        st.session_state.meal_plan = pd.concat([st.session_state.meal_plan, new_row], ignore_index=True)
        st.rerun()

    st.divider()
    
    # --- SMART SUGGESTION ENGINE ---
    st.header("🤖 Smart Clinical Suggestions")
    st.markdown("Algorithmic recommendations that fit remaining caloric and sodium windows while maximizing Potassium/Calcium for vasodilation.")
    
    if rem_kcal > 50 and rem_na > 10:
        # Filter logic: Fits in calories, fits in sodium, sort by DASH impact (K + Ca + Mg)
        safe_foods = df[(df['Energy_kcal'] <= rem_kcal) & (df['Sodium_mg'] <= rem_na)].copy()
        safe_foods['DASH_Score'] = safe_foods['Potassium_mg'] + safe_foods['Calcium_mg'] + safe_foods['Magnesium_mg']
        top_suggestions = safe_foods.sort_values(by='DASH_Score', ascending=False).head(3)
        
        for i, row in top_suggestions.iterrows():
            st.success(f"💡 **{row['Food Item']}** (Per 100g) \n\n ⚡ {row['Energy_kcal']} kcal | 🧂 Na: {row['Sodium_mg']}mg | 🍌 K: {row['Potassium_mg']}mg | 🥛 Ca: {row['Calcium_mg']}mg")
    else:
        st.warning("Daily limits reached. No further food suggestions available.")

# ==========================================
# TAB 3: VISUAL ANALYTICS (DASHBOARD)
# ==========================================
with tab3:
    st.header("Metabolic & DASH Biomarkers")
    
    # MACRO PIE CHART
    st.subheader("Macronutrient AMDR Distribution")
    if curr_kcal > 0:
        macro_labels = ['Protein (kcal)', 'Carbs (kcal)', 'Fats (kcal)']
        macro_vals = [curr_pro * 4, curr_carb * 4, curr_fat * 9]
        fig_pie = px.pie(names=macro_labels, values=macro_vals, hole=0.4, color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99'])
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Log food to see macronutrient visualization.")

    # MICRO RADAR CHART (DASH & ACE Tracking)
    st.subheader("RAAS & Vasodilation Radar")
    st.markdown("Aim to push Potassium, Calcium, and Magnesium to the outer edge, while keeping Sodium strictly inside.")
    
    # Calculate percentages of targets (Cap at 100 for radar shape, except Sodium which we want to see if it overflows)
    pct_na = min((curr_na / max_sodium) * 100, 150) if max_sodium else 0
    pct_k = min((curr_k / target_potassium) * 100, 100) if target_potassium else 0
    pct_ca = min((curr_ca / target_calcium) * 100, 100) if target_calcium else 0
    pct_mg = min((curr_mg / target_magnesium) * 100, 100) if target_magnesium else 0
    
    categories = ['Sodium (Limit)', 'Potassium (Goal)', 'Calcium (Goal)', 'Magnesium (Goal)']
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[pct_na, pct_k, pct_ca, pct_mg],
        theta=categories,
        fill='toself',
        line_color='indigo'
    ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(fig_radar, use_container_width=True)

    # Detailed Readout
    if curr_na > max_sodium: st.error(f"⚠️ SODIUM BREACH: {curr_na:.0f} mg / {max_sodium} mg")
    else: st.write(f"🧂 **Sodium:** {curr_na:.0f} / {max_sodium} mg")
    st.write(f"🍌 **Potassium:** {curr_k:.0f} / {target_potassium} mg")
    st.write(f"🥛 **Calcium:** {curr_ca:.0f} / {target_calcium} mg")
    st.write(f"🥬 **Magnesium:** {curr_mg:.0f} / {target_magnesium} mg")

# ==========================================
# TAB 4: CLINICAL REPORTS & LITERATURE
# ==========================================
with tab4:
    st.header("Patient Intake Log")
    if not st.session_state.meal_plan.empty:
        st.dataframe(st.session_state.meal_plan, use_container_width=True)
        
        # CLINICAL CSV EXPORT
        csv = st.session_state.meal_plan.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Clinical Report (CSV)",
            data=csv,
            file_name="Patient_Metabolic_Report.csv",
            mime="text/csv",
        )
        
        if st.button("🗑️ Clear Patient Log"):
            st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Portion', 'Energy_kcal', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Calcium_mg', 'Magnesium_mg'])
            st.rerun()
    else:
        st.info("No dietary data logged.")

    st.divider()
    with st.expander("📚 Scientific Literature & Equations Used"):
        st.markdown("""
        **Equations & Guidelines:**
        * **BMR/TDEE:** Mifflin-St Jeor Equation (Mifflin et al., 1990, *Am J Clin Nutr*). 
        * **Macronutrient Split:** AMDR guidelines (Institute of Medicine, 2005).
        
        **Genetics (ACE I/D):**
        * **Srivastava et al. (2012)**: *Assoc. of ACE Gene Polymorphism with Essential Hypertension in North Indian Population.*
        * **Poch et al. (2001)**: Confirmed GxE interaction between ACE variants and sodium limits.
        
        **DASH Diet Biomarkers (Ca & Mg):**
        * **Appel et al. (1997)**: *A Clinical Trial of the Effects of Dietary Patterns on Blood Pressure (NEJM).* Established that Calcium and Magnesium are obligatory co-factors alongside Potassium for effective vasodilation.
        """)
