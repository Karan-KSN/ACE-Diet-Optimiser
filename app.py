import streamlit as st
import pandas as pd

# --- 1. SET UP THE NIN CSV DATABASE ---
@st.cache_data
def load_data():
    # Load your specific Kaggle dataset
    df = pd.read_csv('ifct2017_compositions.csv')
    
    # Select only the columns we care about for the macronutrient and micronutrient tracking windows
    df = df[['name', 'protcnt', 'choavldf', 'fatce', 'na', 'k']]
    
    # Rename them so they match the rest of our Streamlit code perfectly
    df.columns = ['Food Item', 'Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg']
    
    # Convert all columns (except the food name) to numbers, forcing any text like 'Tr' (Trace) to become NaN, then fill with 0.
    numeric_cols = ['Protein_g', 'Carbs_g', 'Fat_g', 'Sodium_mg', 'Potassium_mg']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    return df

df = load_data()

# Initialize a "shopping cart" to remember what the user ate today
if 'meal_plan' not in st.session_state:
    st.session_state.meal_plan = pd.DataFrame(columns=['Food Item', 'Sodium_mg', 'Potassium_mg', 'Protein_g', 'Carbs_g', 'Fat_g'])

# --- 2. BUILD THE USER INTERFACE ---
# (Keep the rest of your UI code exactly the same as before!)