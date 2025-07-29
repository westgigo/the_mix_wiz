import streamlit as st
import requests
import random

st.set_page_config(page_title="The Mix Wiz", layout="centered")
st.title("🪄 The Mix Wiz")

# --- Ingredient selection state ---
if "selected_ingredients" not in st.session_state:
    st.session_state["selected_ingredients"] = []

# --- Fetch and cache ingredients ---
@st.cache_data
def fetch_ingredients():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?i=list"
    response = requests.get(url)
    data = response.json()
    return sorted([item['strIngredient1'] for item in data.get('drinks') or []])

# --- Fetch all cocktails from A-Z ---
@st.cache_data
def fetch_all_cocktails():
    cocktails = []
    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"https://www.thecocktaildb.com/api/json/v2/961249867/search.php?f={letter}"
        response = requests.get(url)
        data = response.json()
        if data.get('drinks'):
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
            ing_clean = ing.strip()
            ing_normalized = ing_clean.lower().replace(" ", "_")
            is_missing = ing_normalized not in user_ingredients

            if is_missing:
                missing.append(ing_clean)

            # Ingredient image
            ing_image_url = f"https://www.thecocktaildb.com/images/ingredients/{ing_clean.replace(' ', '%20')}-medium.png"
            display_text = f"{meas.strip()} {ing_clean}" if meas else ing_clean

            # Style red for missing ingredients
            text_color = "red" if is_missing and show_missing else "inherit"

            # Render ingredient with image and fallback
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; margin-bottom: 4px; color: {text_color};'>
                    <img src="{ing_image_url}" width="30" height="30"
                         style="margin-right: 10px; border-radius: 4px;"
                         onerror="this.style.display='none';">
                    <span>{display_text}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

    if show_missing and missing:
        st.warning(f"⚠️ You're missing {len(missing)} ingredient(s): {', '.join(missing)}")

    st.markdown("### Instructions:")
    st.info(cocktail.get("strInstructions", "No instructions available."))


# --- UI: Filters ---
col_title, col_clear = st.columns([10, 1])
with col_title:
    st.markdown("### What ingredients do you have?")
#with col_clear:
#    clear_clicked = st.button("🔄", help="Clear ingredient selection")
#    if clear_clicked:
#        st.session_state["selected_ingredients"] = []
#        st.rerun()

ingredients = fetch_ingredients()
selected_ingredients = st.multiselect(
    "Select your available ingredients:",
    ingredients,
    default=st.session_state["selected_ingredients"],
    help="Pick ingredients you're interested in — what you have or want to explore!"
)
st.session_state["selected_ingredients"] = selected_ingredients
normalized = [ing.lower().replace(" ", "_") for ing in selected_ingredients]

# --- Action Buttons ---
col1, col2, col3, col4 = st.columns(4)

# --- Surprise Me ---
if col1.button("🥂 Surprise me", help="Pick a random cocktail using ANY of your ingredients (or none)"):
    if normalized:
        with st.spinner("Mixing magic with your ingredients..."):
            # Fetch ALL cocktails
            all_cocktails = fetch_all_cocktails()

            # Match ANY of the selected ingredients
            matching = [c for c in all_cocktails if any(i in normalized for i in extract_ingredients(c))]

        if not matching:
            st.error("😥 No cocktails found that use any of those ingredients.")
        else:
            chosen = random.choice(matching)
            show_cocktail(chosen, normalized, show_missing=True)
    else:
        # No ingredients selected → fallback to true random
        with st.spinner("Mixing magic at random..."):
            try:
                response = requests.get("https://www.thecocktaildb.com/api/json/v1/1/random.php")
                data = response.json()
                cocktail = data.get('drinks', [None])[0]
            except Exception as e:
                cocktail = None
                st.error(f"⚠️ Could not fetch a random cocktail: {e}")

        if not cocktail:
            st.error("😵 Couldn't fetch a random cocktail.")
        else:
            show_cocktail(cocktail, user_ingredients=[], show_missing=False)


# --- Show All I Can Make ---
if col2.button("📋 Show all I can make", help="Only cocktails you can make 100% with what you selected"):
    if not normalized:
        st.info("🔍 Please select one or more ingredients to see what you can make.")
    else:
        with st.spinner("Scanning possibilities..."):
            all_cocktails = fetch_all_cocktails()
            possible = [c for c in all_cocktails if all(i in normalized for i in extract_ingredients(c))]

        if not possible:
            st.error("🙁 You can't fully make any cocktails with just those.")
        else:
            for cocktail in possible:
                show_cocktail(cocktail, normalized, show_missing=False)
                st.markdown("---")

# --- Explore With Ingredients ---
if col3.button("🔍 Explore with my ingredients", help="Browse cocktails using ANY of your selected ingredients"):
    if not normalized:
        st.info("🔍 Please select at least one ingredient to explore cocktails.")
    else:
        with st.spinner("Exploring cocktail space..."):
            joined = ",".join(normalized)
            url = f"https://www.thecocktaildb.com/api/json/v2/961249867/filter.php?i={joined}"

            try:
                response = requests.get(url)
                data = response.json()
                ids = [drink['idDrink'] for drink in data.get('drinks') or []]
            except Exception as e:
                st.error(f"⚠️ API error: {e}")
                ids = []

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

# --- Popular Cocktails ---
if col4.button("🌟 Most Popular Cocktails", help="Show latest and popular cocktails just for fun"):
    with st.spinner("Fetching fresh mixes..."):
        urls = [
            "https://www.thecocktaildb.com/api/json/v2/961249867/latest.php",
            "https://www.thecocktaildb.com/api/json/v2/961249867/popular.php"
        ]
        cocktails = []
        for url in urls:
            try:
                res = requests.get(url)
                data = res.json()
                if data.get('drinks'):
                    cocktails.extend(data['drinks'])
            except Exception as e:
                st.error(f"⚠️ Couldn't fetch from {url}: {e}")

    if not cocktails:
        st.error("😞 Couldn't fetch any popular or new drinks.")
    else:
        for cocktail in cocktails:
            show_cocktail(cocktail, [], show_missing=False)
            st.markdown("---")

# --- Manual Cocktail Explorer Dropdown ---
st.markdown("### 🍸 Explore All Cocktails")
all_cocktails = fetch_all_cocktails()
cocktail_lookup = {f"{c['strDrink']} ({c['idDrink']})": c['idDrink'] for c in all_cocktails}
options = ["None"] + list(cocktail_lookup.keys())

selected_label = st.selectbox("Select a cocktail to view:", options)

if selected_label != "None":
    selected_id = cocktail_lookup[selected_label]
    cocktail = next((c for c in all_cocktails if c['idDrink'] == selected_id), None)
    if cocktail:
        show_cocktail(cocktail, user_ingredients=[], show_missing=False)
