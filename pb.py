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

# --- Fetch all cocktails from A-Z ---
@st.cache_data
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

# --- Ingredient selection (shared across pages) ---
with st.expander("🔧 Select Your Ingredients"):
    ingredients = fetch_ingredients()
    selected_ingredients = st.multiselect(
        "Pick what you have or want to explore:",
        ingredients,
        help="Select your available ingredients.",
    )
    normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]

# --- Top Navigation Replacement ---
page = st.radio(
    "Choose a page:",
    ["🥂 Surprise Me", "📋 What Can I Make", "🔍 Explore Ingredients", "🌟 Popular Cocktails", "🍸 Cocktail Explorer"],
    horizontal=True
)

# --- Surprise Me Page ---
if page == "🥂 Surprise Me":
    st.header("Surprise Me!")
    with st.spinner("Mixing magic..."):
        if normalized:
            joined = ",".join(normalized)
            url = f"https://www.thecocktaildb.com/api/json/v2/961249867/filter.php?i={joined}"
        else:
            url = "https://www.thecocktaildb.com/api/json/v2/961249867/randomselection.php"

        response = requests.get(url)
        data = response.json()
        ids = [drink['idDrink'] for drink in data['drinks']] if data['drinks'] else []
        all_cocktails = fetch_all_cocktails()
        filtered = [d for d in all_cocktails if d['idDrink'] in ids]

    if not filtered:
        st.error("😥 No cocktails found with those ingredients.")
    else:
        chosen = random.choice(filtered)
        show_cocktail(chosen, normalized, show_missing=True)

# --- What Can I Make Page ---
elif page == "📋 What Can I Make":
    st.header("Cocktails You Can Fully Make")
    with st.spinner("Checking recipes..."):
        all_cocktails = fetch_all_cocktails()
        possible = [c for c in all_cocktails if all(i in normalized for i in extract_ingredients(c))]

    if not possible:
        st.error("🙁 You can't fully make any cocktails with just those.")
    else:
        for cocktail in possible:
            show_cocktail(cocktail, normalized, show_missing=False)
            st.markdown("---")

# --- Explore with My Ingredients Page ---
elif page == "🔍 Explore Ingredients":
    st.header("Explore with Your Ingredients")
    with st.spinner("Exploring..."):
        if normalized:
            joined = ",".join(normalized)
            url = f"https://www.thecocktaildb.com/api/json/v2/961249867/filter.php?i={joined}"
        else:
            url = "https://www.thecocktaildb.com/api/json/v2/961249867/randomselection.php"

        response = requests.get(url)
        data = response.json()
        ids = [drink['idDrink'] for drink in data['drinks']] if data['drinks'] else []
        all_cocktails = fetch_all_cocktails()
        filtered = [d for d in all_cocktails if d['idDrink'] in ids]

        def count_missing(c):
            return len([i for i in extract_ingredients(c) if i not in normalized])

        sorted_cocktails = sorted(filtered, key=count_missing)

    if not sorted_cocktails:
        st.error("😥 No matches found.")
    else:
        for cocktail in sorted_cocktails:
            show_cocktail(cocktail, normalized, show_missing=True)
            st.markdown("---")

# --- Popular Cocktails Page ---
elif page == "🌟 Popular Cocktails":
    st.header("Popular & Latest Cocktails")
    with st.spinner("Fetching crowd favourites..."):
        urls = [
            "https://www.thecocktaildb.com/api/json/v2/961249867/latest.php",
            "https://www.thecocktaildb.com/api/json/v2/961249867/popular.php"
        ]
        cocktails = []
        for url in urls:
            res = requests.get(url)
            data = res.json()
            if data['drinks']:
                cocktails.extend(data['drinks'])

    if not cocktails:
        st.error("😞 Couldn't fetch any popular or new drinks.")
    else:
        for cocktail in cocktails:
            show_cocktail(cocktail, [], show_missing=False)
            st.markdown("---")

# --- Manual Explorer Dropdown Page ---
elif page == "🍸 Cocktail Explorer":
    st.header("Explore All Cocktails")
    all_cocktails = fetch_all_cocktails()
    all_names = sorted([(c['strDrink'], c['idDrink']) for c in all_cocktails])
    selected = st.selectbox("Select a cocktail to view:", ["None"] + [name for name, _ in all_names])

    if selected != "None":
        cocktail = next((c for c in all_cocktails if c['strDrink'] == selected), None)
        if cocktail:
            show_cocktail(cocktail, user_ingredients=[], show_missing=False)
