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

@st.cache_data
def fetch_glasses():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?g=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strGlass'] for item in data['drinks']])

@st.cache_data
def fetch_categories():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?c=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strCategory'] for item in data['drinks']])

@st.cache_data
def fetch_alcohol_types():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?a=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strAlcoholic'] for item in data['drinks']])

# --- Fetch all cocktails from a-z ---
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

# --- UI: Filters ---
st.markdown("### What ingredients do you have?")
ingredients = fetch_ingredients()
selected_ingredients = st.multiselect(
    "Select your available ingredients:",
    ingredients,
    help="Pick ingredients you're interested in — what you have or want to explore!"
)

glass_filter = st.selectbox(
    "Optional: Choose a glass type to filter cocktails (or leave empty):",
    ["Any"] + fetch_glasses()
)

category_filter = st.selectbox(
    "Optional: Choose a category (or leave empty):",
    ["Any"] + fetch_categories()
)

alcohol_filter = st.selectbox(
    "Optional: Choose alcohol content:",
    ["Any"] + fetch_alcohol_types()
)

# --- Action Buttons ---
col1, col2, col3, col4 = st.columns(4)

# --- Apply filters ---
def apply_filters(cocktails):
    if glass_filter != "Any":
        cocktails = [c for c in cocktails if c.get('strGlass') == glass_filter]
    if category_filter != "Any":
        cocktails = [c for c in cocktails if c.get('strCategory') == category_filter]
    if alcohol_filter != "Any":
        cocktails = [c for c in cocktails if c.get('strAlcoholic') == alcohol_filter]
    return cocktails

if col1.button("🥂 Surprise me", help="Pick a random cocktail using ANY of your ingredients (or none)"):
    with st.spinner("Mixing magic..."):
        normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
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
        filtered = apply_filters(filtered)

    if not filtered:
        st.error("😥 No cocktails found with those ingredients.")
    else:
        chosen = random.choice(filtered)
        show_cocktail(chosen, normalized, show_missing=True)

if col2.button("📋 Show all I can make", help="Only cocktails you can make 100% with what you selected"):
    with st.spinner("Scanning possibilities..."):
        all_cocktails = fetch_all_cocktails()
        normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
        possible = [c for c in all_cocktails if all(i in normalized for i in extract_ingredients(c))]
        possible = apply_filters(possible)

    if not possible:
        st.error("🙁 You can't fully make any cocktails with just those.")
    else:
        for cocktail in possible:
            show_cocktail(cocktail, normalized, show_missing=False)
            st.markdown("---")

if col3.button("🔍 Explore with my ingredients", help="Browse cocktails using ANY of your selected ingredients"):
    with st.spinner("Exploring cocktail space..."):
        normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]
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
        filtered = apply_filters(filtered)

        def count_missing(c):
            return len([i for i in extract_ingredients(c) if i not in normalized])

        sorted_cocktails = sorted(filtered, key=count_missing)

    if not sorted_cocktails:
        st.error("😥 No matches found.")
    else:
        for cocktail in sorted_cocktails:
            show_cocktail(cocktail, normalized, show_missing=True)
            st.markdown("---")

if col4.button("🌟 More magic", help="Show latest and popular cocktails just for fun"):
    with st.spinner("Fetching fresh mixes..."):
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

        cocktails = apply_filters(cocktails)

    if not cocktails:
        st.error("😞 Couldn't fetch any popular or new drinks.")
    else:
        for cocktail in cocktails:
            show_cocktail(cocktail, [], show_missing=False)
            st.markdown("---")