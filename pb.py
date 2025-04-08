import streamlit as st
import requests
import random

st.set_page_config(page_title="The Mix Wiz", layout="centered")
st.title("🪄 The Mix Wiz")

# --- Fetch and cache ingredients ---
@st.cache_data

def fetch_ingredients():
    url = "https://www.thecocktaildb.com/api/json/v1/1/list.php?i=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strIngredient1'] for item in data['drinks']])

# --- Fetch all cocktails from a-z ---
def fetch_all_cocktails():
    cocktails = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"https://www.thecocktaildb.com/api/json/v1/1/search.php?f={letter}"
        response = requests.get(url)
        data = response.json()
        if data['drinks']:
            cocktails.extend(data['drinks'])
    return cocktails

# --- Extract ingredients from a cocktail object ---
def extract_ingredients(cocktail):
    ingredients = []
    for i in range(1, 16):
        ing = cocktail.get(f"strIngredient{i}")
        if ing and ing.strip():
            ingredients.append(ing.strip().lower().replace(" ", "_"))
    return ingredients

# --- Get matching cocktails ---
def find_matching_cocktails(user_ingredients, all_cocktails):
    matches = []
    for drink in all_cocktails:
        drink_ings = extract_ingredients(drink)
        if all(ing in user_ingredients for ing in drink_ings):
            matches.append(drink)
    return matches

# UI: Ingredient selection
st.markdown("### What ingredients do you have?")
ingredients = fetch_ingredients()
selected_ingredients = st.multiselect(
    "Select one or more ingredients:",
    ingredients,
    help="These are the ingredients you currently have."
)

# Button to search
if st.button("🍹 Make me a cocktail!"):
    if not selected_ingredients:
        st.warning("Please select at least one ingredient.")
    else:
        with st.spinner("Searching delicious options..."):
            all_cocktails = fetch_all_cocktails()
            normalized_ingredients = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
            possible = find_matching_cocktails(normalized_ingredients, all_cocktails)

        if not possible:
            st.error("😢 Sorry, no cocktails can be made with those ingredients.")
        else:
            chosen = random.choice(possible)
            st.subheader(chosen['strDrink'])
            st.image(chosen['strDrinkThumb'], width=300)

            st.markdown("### Ingredients:")
            for i in range(1, 16):
                ing = chosen.get(f"strIngredient{i}")
                meas = chosen.get(f"strMeasure{i}")
                if ing and ing.strip():
                    line = f"- {meas.strip()} {ing.strip()}" if meas else f"- {ing.strip()}"
                    st.markdown(line)

            st.markdown("### Instructions:")
            st.info(chosen.get("strInstructions", "No instructions available."))
