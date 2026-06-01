import json
import random

import requests
import streamlit as st
from streamlit_local_storage import LocalStorage


st.set_page_config(page_title="The Mix Wiz", page_icon="🪄", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }
    div.stButton > button {
        min-height: 3rem;
        border-radius: 8px;
        font-weight: 650;
    }
    div[data-testid="stImage"] img {
        border-radius: 8px;
    }
    .drink-card {
        border: 1px solid rgba(49, 51, 63, 0.18);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0 1.25rem;
        background: rgba(250, 250, 250, 0.65);
    }
    .ingredient-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-bottom: 0.3rem;
    }
    .ingredient-row img {
        width: 32px;
        height: 32px;
        border-radius: 4px;
        object-fit: contain;
    }
    .missing {
        color: #b42318;
        font-weight: 600;
    }
    div[data-testid="element-container"]:has(iframe[title="streamlit_local_storage.st_local_storage"]) {
        display: none;
    }
    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🪄 The Mix Wiz")

FAVOURITES_STORAGE_KEY = "mixwiz_favourites"


def normalise_ingredient(ingredient):
    return ingredient.strip().lower().replace(" ", "_")


@st.cache_data(ttl=60 * 60 * 24)
def fetch_json(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60 * 60 * 24)
def fetch_ingredients():
    url = "https://www.thecocktaildb.com/api/json/v2/961249867/list.php?i=list"
    data = fetch_json(url)
    return sorted([item["strIngredient1"] for item in data.get("drinks") or []])


@st.cache_data(ttl=60 * 60 * 24)
def fetch_all_cocktails():
    cocktails = []
    seen_ids = set()

    for letter in "abcdefghijklmnopqrstuvwxyz":
        url = f"https://www.thecocktaildb.com/api/json/v2/961249867/search.php?f={letter}"
        data = fetch_json(url)
        for cocktail in data.get("drinks") or []:
            cocktail_id = cocktail.get("idDrink")
            if cocktail_id and cocktail_id not in seen_ids:
                cocktails.append(cocktail)
                seen_ids.add(cocktail_id)

    return cocktails


def fetch_random_cocktail():
    data = fetch_json("https://www.thecocktaildb.com/api/json/v1/1/random.php")
    return data.get("drinks", [None])[0]


def extract_ingredients(cocktail):
    ingredients = []
    for i in range(1, 16):
        ingredient = cocktail.get(f"strIngredient{i}")
        if ingredient and ingredient.strip():
            ingredients.append(normalise_ingredient(ingredient))
    return ingredients


def parse_favourites(raw_favourites):
    try:
        if isinstance(raw_favourites, str):
            favourites = json.loads(raw_favourites) if raw_favourites else []
        elif isinstance(raw_favourites, list):
            favourites = raw_favourites
        else:
            favourites = []
    except (TypeError, json.JSONDecodeError):
        favourites = []

    return [item for item in favourites if isinstance(item, str)]


def load_favourites():
    return parse_favourites(local_storage.getItem(FAVOURITES_STORAGE_KEY))


def save_favourites():
    st.session_state["storage_write_count"] += 1
    storage_key = f"save_favourites_{st.session_state['storage_write_count']}"
    favourites = st.session_state["favourites"]

    if favourites:
        local_storage.setItem(
            FAVOURITES_STORAGE_KEY,
            json.dumps(favourites),
            key=storage_key,
        )
    else:
        local_storage.eraseItem(FAVOURITES_STORAGE_KEY, key=storage_key)


def toggle_favourite(cocktail_id):
    favourites = set(st.session_state["favourites"])
    if cocktail_id in favourites:
        favourites.remove(cocktail_id)
    else:
        favourites.add(cocktail_id)

    st.session_state["favourites"] = sorted(favourites)
    save_favourites()


def set_view(view_name):
    st.session_state["view"] = view_name


def ingredient_display_rows(cocktail, user_ingredients, show_missing):
    missing = []

    for i in range(1, 16):
        ingredient = cocktail.get(f"strIngredient{i}")
        measure = cocktail.get(f"strMeasure{i}")
        if not ingredient or not ingredient.strip():
            continue

        ingredient_clean = ingredient.strip()
        ingredient_normalised = normalise_ingredient(ingredient_clean)
        is_missing = ingredient_normalised not in user_ingredients

        if is_missing:
            missing.append(ingredient_clean)

        image_url = (
            "https://www.thecocktaildb.com/images/ingredients/"
            f"{ingredient_clean.replace(' ', '%20')}-medium.png"
        )
        display_text = f"{measure.strip()} {ingredient_clean}" if measure else ingredient_clean
        text_class = "missing" if is_missing and show_missing else ""

        st.markdown(
            f"""
            <div class="ingredient-row {text_class}">
                <img src="{image_url}" onerror="this.style.display='none';">
                <span>{display_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return missing


def show_cocktail(cocktail, user_ingredients, show_missing=True, key_suffix=""):
    cocktail_id = cocktail["idDrink"]
    favourite_key = f"fav_{cocktail_id}_{key_suffix}"
    is_favourite = cocktail_id in st.session_state["favourites"]

    with st.container():
        st.markdown('<div class="drink-card">', unsafe_allow_html=True)

        title_col, fav_col = st.columns([8, 1])
        with title_col:
            st.subheader(cocktail["strDrink"])
        with fav_col:
            st.button(
                "★" if is_favourite else "☆",
                key=favourite_key,
                help="Save to favourites on this device",
                on_click=toggle_favourite,
                args=(cocktail_id,),
                use_container_width=True,
            )

        image_col, details_col = st.columns([1, 2])
        with image_col:
            st.image(cocktail["strDrinkThumb"], use_container_width=True)
        with details_col:
            st.markdown("#### Ingredients")
            missing = ingredient_display_rows(cocktail, user_ingredients, show_missing)

            if show_missing and missing:
                st.warning(
                    f"You're missing {len(missing)} ingredient(s): {', '.join(missing)}"
                )

            st.markdown("#### Instructions")
            st.info(cocktail.get("strInstructions", "No instructions available."))

        st.markdown("</div>", unsafe_allow_html=True)


def show_cocktail_list(cocktails, user_ingredients, show_missing=True, key_prefix="list"):
    for index, cocktail in enumerate(cocktails):
        show_cocktail(
            cocktail,
            user_ingredients,
            show_missing=show_missing,
            key_suffix=f"{key_prefix}_{index}",
        )


local_storage = LocalStorage(key="mixwiz_storage")

if "selected_ingredients" not in st.session_state:
    st.session_state["selected_ingredients"] = []
if "storage_write_count" not in st.session_state:
    st.session_state["storage_write_count"] = 0
if "favourites" not in st.session_state:
    st.session_state["favourites"] = load_favourites()
if "view" not in st.session_state:
    st.session_state["view"] = "explore"

ingredients = fetch_ingredients()
all_cocktails = fetch_all_cocktails()
cocktails_by_id = {cocktail["idDrink"]: cocktail for cocktail in all_cocktails}

st.markdown("### What ingredients do you have?")
selected_ingredients = st.multiselect(
    "Select your available ingredients:",
    ingredients,
    key="selected_ingredients",
    placeholder="Search ingredients",
    help="Pick ingredients you have or want to explore.",
)
normalised_ingredients = [normalise_ingredient(item) for item in selected_ingredients]

action_cols = st.columns(4)
with action_cols[0]:
    st.button(
        "🥂 Surprise me",
        help="Pick a random cocktail using any of your ingredients.",
        on_click=set_view,
        args=("surprise",),
        use_container_width=True,
    )
with action_cols[1]:
    st.button(
        "📋 I can make",
        help="Only cocktails you can make 100% with what you selected.",
        on_click=set_view,
        args=("make",),
        use_container_width=True,
    )
with action_cols[2]:
    st.button(
        "🔍 Explore",
        help="Browse cocktails using any of your selected ingredients.",
        on_click=set_view,
        args=("explore",),
        use_container_width=True,
    )
with action_cols[3]:
    st.button(
        "🌟 Popular",
        help="Show popular and latest cocktails.",
        on_click=set_view,
        args=("popular",),
        use_container_width=True,
    )

find_tab, favourites_tab, all_tab = st.tabs(["Find drinks", "Favourites", "All cocktails"])

with find_tab:
    view = st.session_state["view"]

    if view == "surprise":
        try:
            with st.spinner("Mixing magic..."):
                if normalised_ingredients:
                    matching = [
                        cocktail
                        for cocktail in all_cocktails
                        if any(
                            ingredient in normalised_ingredients
                            for ingredient in extract_ingredients(cocktail)
                        )
                    ]
                    cocktail = random.choice(matching) if matching else None
                    show_missing = True
                else:
                    cocktail = fetch_random_cocktail()
                    show_missing = False

            if cocktail:
                show_cocktail(
                    cocktail,
                    normalised_ingredients,
                    show_missing=show_missing,
                    key_suffix="surprise",
                )
            else:
                st.error("No cocktails found that use those ingredients.")
        except requests.RequestException as error:
            st.error(f"Could not fetch a cocktail: {error}")

    elif view == "make":
        if not normalised_ingredients:
            st.info("Select one or more ingredients to see what you can make.")
        else:
            possible = [
                cocktail
                for cocktail in all_cocktails
                if all(
                    ingredient in normalised_ingredients
                    for ingredient in extract_ingredients(cocktail)
                )
            ]

            if possible:
                st.success(f"You can make {len(possible)} cocktail(s).")
                show_cocktail_list(
                    possible,
                    normalised_ingredients,
                    show_missing=False,
                    key_prefix="make",
                )
            else:
                st.error("You cannot fully make any cocktails with just those ingredients.")

    elif view == "popular":
        try:
            with st.spinner("Fetching fresh mixes..."):
                cocktails = []
                seen_ids = set()
                for url in [
                    "https://www.thecocktaildb.com/api/json/v2/961249867/latest.php",
                    "https://www.thecocktaildb.com/api/json/v2/961249867/popular.php",
                ]:
                    data = fetch_json(url)
                    for cocktail in data.get("drinks") or []:
                        cocktail_id = cocktail.get("idDrink")
                        if cocktail_id and cocktail_id not in seen_ids:
                            cocktails.append(cocktail)
                            seen_ids.add(cocktail_id)

            if cocktails:
                show_cocktail_list(
                    cocktails,
                    normalised_ingredients,
                    show_missing=False,
                    key_prefix="popular",
                )
            else:
                st.error("Could not fetch popular or new drinks.")
        except requests.RequestException as error:
            st.error(f"Could not fetch popular drinks: {error}")

    else:
        if not normalised_ingredients:
            st.info("Select at least one ingredient, then use Explore or Surprise me.")
        else:
            def count_missing(cocktail):
                return len(
                    [
                        ingredient
                        for ingredient in extract_ingredients(cocktail)
                        if ingredient not in normalised_ingredients
                    ]
                )

            matching = [
                cocktail
                for cocktail in all_cocktails
                if any(
                    ingredient in normalised_ingredients
                    for ingredient in extract_ingredients(cocktail)
                )
            ]
            matching = sorted(matching, key=count_missing)

            if matching:
                st.success(f"Found {len(matching)} cocktail(s) using your ingredients.")
                show_cocktail_list(
                    matching,
                    normalised_ingredients,
                    show_missing=True,
                    key_prefix="explore",
                )
            else:
                st.error("No matches found.")

with favourites_tab:
    st.caption(
        "Favourites are saved only in this browser on this device. "
        "The Mix Wiz does not send them to, or store them on, a platform account or database."
    )

    favourite_cocktails = [
        cocktails_by_id[cocktail_id]
        for cocktail_id in st.session_state["favourites"]
        if cocktail_id in cocktails_by_id
    ]

    if favourite_cocktails:
        show_cocktail_list(
            favourite_cocktails,
            normalised_ingredients,
            show_missing=False,
            key_prefix="favourites",
        )
    else:
        st.info("No favourites yet. Use the star on a cocktail to save it here.")

with all_tab:
    cocktail_lookup = {
        f"{cocktail['strDrink']} ({cocktail['idDrink']})": cocktail["idDrink"]
        for cocktail in all_cocktails
    }
    options = ["None"] + list(cocktail_lookup.keys())
    selected_label = st.selectbox("Select a cocktail to view:", options)

    if selected_label != "None":
        selected_id = cocktail_lookup[selected_label]
        show_cocktail(
            cocktails_by_id[selected_id],
            normalised_ingredients,
            show_missing=False,
            key_suffix="manual",
        )
