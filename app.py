import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SET UP THE NIN CSV DATABASE ---
@st.cache_data
def load_data():
    df = pd.read_csv('ifct2017_compositions.csv')
    df = df[['name', 'protcnt', 'choavldf', 'fatce', 'na', 'k', 'enerc', 'ca', 'mg']]
    df.columns = ['Food Item', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal', 'Calcium_mg', 'Magnesium_mg']
    
    numeric_cols = ['Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Energy_kcal', 'Calcium_mg', 'Magnesium_mg']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    # INJECT WATER INTO THE DATABASE
    water_row = pd.DataFrame([{
        'Food Item': '💧 Water, potable (Tap/RO)', 
        'Protein_g': 0.0, 'Carbs_g': 0.0, 'Fat_g': 0.0, 
        'Sodium_mg': 0.0, 'Potassium_mg': 0.0, 'Energy_kcal': 0.0, 
        'Calcium_mg': 0.0, 'Magnesium_mg': 0.0
    }])
    df = pd.concat([water_row, df], ignore_index=True)
    return df

df = load_data()

# --- 2. INITIALIZE SESSION STATES ---
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=[
        'Food Item', 'Portion', 'Energy_kcal', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Calcium_mg', 'Magnesium_mg'
    ])

if 'custom_recipes' not in st.session_state:
    st.session_state.custom_recipes = pd.DataFrame(columns=df.columns)

if 'recipe_builder' not in st.session_state:
    st.session_state.recipe_builder = pd.DataFrame(columns=[
        'Ingredient', 'Grams', 'Energy_kcal', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg', 'Calcium_mg', 'Magnesium_mg'
    ])

combined_df = pd.concat([df, st.session_state.custom_recipes], ignore_index=True)

# --- 3. BUILD THE UI & TABS ---
st.set_page_config(page_title="Nutrigenetic CDSS", layout="centered")
st.title("🧬 Clinical Nutrigenetic CDSS")
st.markdown("Automated IFCT tracking, DASH Biomarkers, & ACE GxE Interactions.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Patient Setup", "👨‍🍳 Recipe Builder", "🍲 Diet Log", "📊 Analytics", "📄 Reports"])

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
    target_calcium = 1000
    target_magnesium = 400

# ==========================================
# TAB 2: RECIPE BUILDER
# ==========================================
with tab2:
    st.header("👨‍🍳 Custom Composite Recipe Engine")
    st.markdown("Combine raw IFCT ingredients to build real household dishes. The algorithm normalizes your dish to a 100g standard.")
    
    recipe_ingredient = st.selectbox("Select Raw Ingredient:", df['Food Item'])
    
    col1, col2 = st.columns(2)
    with col1:
        rec_portion_type = st.selectbox("Select Unit:", ["Grams", "Milliliters (ml)"], key="rec_port")
    with col2:
        unit_label = "ml" if "ml" in rec_portion_type else "Grams"
        recipe_grams = st.number_input(f"Enter exact {unit_label}:", min_value=1.0, value=50.0, key="rec_grams")
    
    if st.button("➕ Add to Mixing Bowl"):
        base = df[df['Food Item'] == recipe_ingredient].iloc[0]
        mult = recipe_grams / 100.0
        new_ing = pd.DataFrame([{
            'Ingredient': recipe_ingredient, 'Grams': recipe_grams,
            'Energy_kcal': base['Energy_kcal'] * mult, 'Protein_g': base['Protein_g'] * mult,
            'Carbs_g': base['Carbs_g'] * mult, 'Fat_g': base['Fat_g'] * mult,
            'Sodium_mg': base['Sodium_mg'] * mult, 'Potassium_mg': base['Potassium_mg'] * mult,
            'Calcium_mg': base['Calcium_mg'] * mult, 'Magnesium_mg': base['Magnesium_mg'] * mult
        }])
        st.session_state.recipe_builder = pd.concat([st.session_state.recipe_builder, new_ing], ignore_index=True)
        st.rerun()

    if not st.session_state.recipe_builder.empty:
        st.subheader("Current Mixing Bowl")
        st.dataframe(st.session_state.recipe_builder[['Ingredient', 'Grams', 'Energy_kcal', 'Protein_g', 'Sodium_mg']], use_container_width=True)
        
        total_weight = st.session_state.recipe_builder['Grams'].sum()
        st.write(f"⚖️ **Total Raw Weight/Volume:** {total_weight:.1f} g/ml")
        
        st.divider()
        recipe_name = st.text_input("Name Your Dish (e.g., Dal Makhani, Roti):", "")
        
        if st.button("💾 Save Recipe to Database", type="primary"):
            if recipe_name != "":
                totals = st.session_state.recipe_builder.sum(numeric_only=True)
                norm_mult = 100.0 / total_weight
                
                final_recipe = pd.DataFrame([{
                    'Food Item': f"🍲 {recipe_name} (Custom)", 
                    'Protein_g': round(totals['Protein_g'] * norm_mult, 2),
                    'Carbs_g': round(totals['Carbs_g'] * norm_mult, 2),
                    'Fat_g': round(totals['Fat_g'] * norm_mult, 2),
                    'Sodium_mg': round(totals['Sodium_mg'] * norm_mult, 2),
                    'Potassium_mg': round(totals['Potassium_mg'] * norm_mult, 2),
                    'Energy_kcal': round(totals['Energy_kcal'] * norm_mult, 2),
                    'Calcium_mg': round(totals['Calcium_mg'] * norm_mult, 2),
                    'Magnesium_mg': round(totals['Magnesium_mg'] * norm_mult, 2)
                }])
                
                st.session_state.custom_recipes = pd.concat([st.session_state.custom_recipes, final_recipe], ignore_index=True)
                st.session_state.recipe_builder = pd.DataFrame(columns=st.session_state.recipe_builder.columns)
                st.success(f"'{recipe_name}' saved! It is now permanently available in the Diet Log tab.")
            else:
                st.error("Please enter a name for your recipe.")
                
        if st.button("🗑️ Empty Mixing Bowl"):
            st.session_state.recipe_builder = pd.DataFrame(columns=st.session_state.recipe_builder.columns)
            st.rerun()

# ==========================================
# TAB 3: DIETARY INTAKE & LOGGING
# ==========================================
with tab3:
    st.header("Log Daily Food Intake")
    portions = {
        "Grams (Custom Entry)": 100, 
        "Milliliters (ml - Liquids)": 100,
        "1 Katori (~150g)": 150, 
        "1 Medium Cup (~250g)": 250, 
        "1 Tablespoon (~15g)": 15, 
        "1 Roti/Piece (~40g)": 40
    }
    
    selected_food = st.selectbox("Search Database (Includes Custom Recipes):", combined_df['Food Item'])
    
    col1, col2 = st.columns(2)
    with col1:
        portion_type = st.selectbox("Select Portion Unit:", list(portions.keys()), key="log_port")
    with col2:
        if portion_type in ["Grams (Custom Entry)", "Milliliters (ml - Liquids)"]:
            unit_label = "ml" if "ml" in portion_type else "Grams"
            grams_input = st.number_input(f"Enter exact {unit_label}:", min_value=1.0, value=100.0, key="log_grams")
        else:
            grams_input = portions[portion_type]
            st.number_input("Equivalent Grams/ml:", value=float(grams_input), disabled=True, key="log_grams_auto")

    if st.button("➕ Add to Window", use_container_width=True):
        base = combined_df[combined_df['Food Item'] == selected_food].iloc[0]
        mult = grams_input / 100.0
        new_row = pd.DataFrame([{
            'Food Item': selected_food, 'Portion': f"{grams_input}g/ml",
            'Energy_kcal': round(base['Energy_kcal'] * mult, 1), 'Protein_g': round(base['Protein_g'] * mult, 1),
            'Carbs_g': round(base['Carbs_g'] * mult, 1), 'Fat_g': round(base['Fat_g'] * mult, 1),
            'Sodium_mg': round(base['Sodium_mg'] * mult, 1), 'Potassium_mg': round(base['Potassium_mg'] * mult, 1),
            'Calcium_mg': round(base['Calcium_mg'] * mult, 1), 'Magnesium_mg': round(base['Magnesium_mg'] * mult, 1)
        }])
        st.session_state.meal_plan = pd.concat([st.session_state.meal_plan, new_row], ignore_index=True)
        st.rerun()

# ==========================================
# CALCULATE LIVE TOTALS (This was missing!)
# ==========================================
curr_kcal = st.session_state.meal_plan['Energy_kcal'].sum() if not st.session_state.meal_plan.empty else 0
curr_pro = st.session_state.meal_plan['Protein_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_carb = st.session_state.meal_plan['Carbs_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_fat = st.session_state.meal_plan['Fat_g'].sum() if not st.session_state.meal_plan.empty else 0
curr_na = st.session_state.meal_plan['Sodium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_k = st.session_state.meal_plan['Potassium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_ca = st.session_state.meal_plan['Calcium_mg'].sum() if not st.session_state.meal_plan.empty else 0
curr_mg = st.session_state.meal_plan['Magnesium_mg'].sum() if not st.session_state.meal_plan.empty else 0

# ==========================================
# TAB 4: VISUAL ANALYTICS
# ==========================================
with tab4:
    st.header("Metabolic & DASH Biomarkers")
    
    st.subheader("Macronutrient AMDR Distribution")
    if curr_kcal > 0:
        macro_labels = ['Protein (kcal)', 'Carbs (kcal)', 'Fats (kcal)']
        macro_vals = [curr_pro * 4, curr_carb * 4, curr_fat * 9]
        fig_pie = px.pie(names=macro_labels, values=macro_vals, hole=0.4, color_discrete_sequence=['#FF9999', '#66B2FF', '#99FF99'])
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Log food to see macronutrient visualization.")

    st.subheader("RAAS & Vasodilation Radar")
    pct_na = min((curr_na / max_sodium) * 100, 150) if max_sodium else 0
    pct_k = min((curr_k / target_potassium) * 100, 100) if target_potassium else 0
    pct_ca = min((curr_ca / target_calcium) * 100, 100) if target_calcium else 0
    pct_mg = min((curr_mg / target_magnesium) * 100, 100) if target_magnesium else 0
    
    categories = ['Sodium (Limit)', 'Potassium (Goal)', 'Calcium (Goal)', 'Magnesium (Goal)']
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=[pct_na, pct_k, pct_ca, pct_mg], theta=categories, fill='toself', line_color='indigo'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
    st.plotly_chart(fig_radar, use_container_width=True)

    if curr_na > max_sodium: st.error(f"⚠️ SODIUM BREACH: {curr_na:.0f} mg / {max_sodium} mg")
    else: st.write(f"🧂 **Sodium:** {curr_na:.0f} / {max_sodium} mg")

# ==========================================
# TAB 5: CLINICAL REPORTS
# ==========================================
with tab5:
    st.header("Patient Intake Log")
    if not st.session_state.meal_plan.empty:
        st.dataframe(st.session_state.meal_plan, use_container_width=True)
        csv = st.session_state.meal_plan.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Clinical Report (CSV)", data=csv, file_name="Patient_Report.csv", mime="text/csv")
        
        if st.button("🗑️ Clear Patient Log"):
            st.session_state.meal_plan = pd.DataFrame(columns=st.session_state.meal_plan.columns)
            st.rerun()
    else:
        st.info("No dietary data logged.")
