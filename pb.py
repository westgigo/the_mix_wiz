import streamlit as st
import requests
import random

st.set_page_config(page_title="The Mix Wiz", layout="centered")
st.title("🪄 The Mix Wiz")

# --- Fetch and cache ingredients ---
@st.cache_data
def fetch_ingredients():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?i=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strIngredient1'] for item in data['drinks']])

# --- Fetch all cocktails from a-z ---
def fetch_all_cocktails():
    cocktails = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"https://www.thecocktaildb.com/api/json/v2/961249867/search.php?f={letter}"
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

# --- Count missing ingredients ---
def count_missing_ingredients(cocktail, user_ingredients):
    drink_ings = extract_ingredients(cocktail)
    return len([ing for ing in drink_ings if ing not in user_ingredients])

# --- Display cocktail ---
def show_cocktail(cocktail, user_ingredients, show_missing=True):
    st.subheader(cocktail['strDrink'])
    st.image(cocktail['strDrinkThumb'], width=300)

    st.markdown("### Ingredients:")
    missing = []
    for i in range(1, 16):
        ing = cocktail.get(f"strIngredient{i}")
        meas = cocktail.get(f"strMeasure{i}")
        if ing and ing.strip():
            ing_normalized = ing.strip().lower().replace(" ", "_")
            if ing_normalized not in user_ingredients:
                missing.append(ing.strip())
            line = f"- {meas.strip()} {ing.strip()}" if meas else f"- {ing.strip()}"
            st.markdown(line)

    if show_missing and missing:
        st.warning(f"⚠️ You're missing {len(missing)} ingredient(s): {', '.join(missing)}")

    st.markdown("### Instructions:")
    st.info(cocktail.get("strInstructions", "No instructions available."))

# --- UI: Ingredient selection ---
st.markdown("### What ingredients do you have?")
ingredients = fetch_ingredients()
selected_ingredients = st.multiselect(
    "Select your available ingredients:",
    ingredients,
    help="These are the ingredients you currently have."
)

# --- Action Buttons ---
col1, col2, col3 = st.columns(3)

if col1.button("🥂 Surprise me", help="Pick a random cocktail using ANY of your ingredients"):
    if not selected_ingredients:
        st.warning("Please select at least one ingredient.")
    else:
        with st.spinner("Mixing magic..."):
            all_cocktails = fetch_all_cocktails()
            normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
            possible = [c for c in all_cocktails if any(i in extract_ingredients(c) for i in normalized)]

        if not possible:
            st.error("😥 No cocktails found with those ingredients.")
        else:
            chosen = random.choice(possible)
            show_cocktail(chosen, normalized, show_missing=True)

if col2.button("📋 Show all I can make", help="Only cocktails you can make 100% with what you selected"):
    if not selected_ingredients:
        st.warning("Please select at least one ingredient.")
    else:
        with st.spinner("Scanning possibilities..."):
            all_cocktails = fetch_all_cocktails()
            normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
            possible = [c for c in all_cocktails if all(i in normalized for i in extract_ingredients(c))]

        if not possible:
            st.error("🙁 You can't fully make any cocktails with just those.")
        else:
            for cocktail in possible:
                show_cocktail(cocktail, normalized, show_missing=False)
                st.markdown("---")

if col3.button("🔍 Explore with my ingredients", help="Browse cocktails using ANY of your selected ingredients"):
    if not selected_ingredients:
        st.warning("Please select at least one ingredient.")
    else:
        with st.spinner("Exploring cocktail space..."):
            all_cocktails = fetch_all_cocktails()
            normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
            possible = [c for c in all_cocktails if any(i in extract_ingredients(c) for i in normalized)]

        if not possible:
            st.error("😥 No matches found.")
        else:
            # Sort cocktails by number of missing ingredients (ascending)
            possible.sort(key=lambda c: count_missing_ingredients(c, normalized))

            for cocktail in possible:
                show_cocktail(cocktail, normalized, show_missing=True)
                st.markdown("---")