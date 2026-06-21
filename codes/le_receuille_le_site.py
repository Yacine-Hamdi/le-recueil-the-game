import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import random
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

st.set_page_config(
    page_title="THE GAME",
    page_icon="🎲",
    layout="centered"
)

st.markdown("""
<style>
.main-title {
    text-align: center;
    font-size: 46px;
    font-weight: 900;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    opacity: 0.75;
    margin-bottom: 30px;
}

.quote-card {
    border-radius: 18px;
    padding: 32px;
    margin: 25px 0;
    text-align: center;
    border: 1px solid rgba(128,128,128,0.25);
}

.quote-text {
    font-size: 34px;
    font-weight: 800;
    line-height: 1.35;
}

.reveal-block {
    animation: fadeIn 0.7s ease-in-out;
}

.person-label {
    text-align: center;
    font-size: 20px;
    font-weight: 800;
    margin-top: 10px;
}

.mobile-answer {
    border-radius: 14px;
    padding: 14px;
    margin: 10px 0;
    text-align: center;
    font-size: 18px;
    font-weight: 700;
    border: 1px solid rgba(128,128,128,0.25);
}

.date-card {
    border-radius: 14px;
    padding: 12px;
    margin: 20px 0;
    text-align: center;
    font-size: 22px;
    font-weight: 800;
    border: 1px solid rgba(128,128,128,0.25);
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG GOOGLE SHEETS
# ============================================================

SHEET_ID = "1d2NR7tnlHcyeAWEKgvdoMAbebPwGxaUcXVj41DAgJjI"
WORKSHEET_NAME = "citations"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_worksheet():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(SHEET_ID)
    return spreadsheet.worksheet(WORKSHEET_NAME)


@st.cache_data(ttl=60)
def load_data_from_sheet():
    worksheet = get_worksheet()
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)

    df["date_message"] = pd.to_datetime(df["date_message"], errors="coerce")
    df["date_complete"] = df["date_message"].dt.strftime("%d/%m/%Y")
    df["annee"] = df["annee"].astype(str)

    return df


df = load_data_from_sheet()

# ============================================================
# CHEMINS IMAGES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

IMG_DIR = BASE_DIR / "img_png"
AUT_IMG_DIR = IMG_DIR / "aut_png"
DEN_IMG_DIR = IMG_DIR / "den_png"
PLACEHOLDER_IMG = IMG_DIR / "Placeholder.png"


def get_person_image_path(name, folder):
    image_path = folder / f"{name}.png"

    if image_path.exists():
        return image_path

    return PLACEHOLDER_IMG


def load_square_image(image_path, size=200):
    img = Image.open(image_path).convert("RGBA")
    img.thumbnail((size, size), Image.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))

    x = (size - img.width) // 2
    y = (size - img.height) // 2

    canvas.paste(img, (x, y), img)

    return canvas


# ============================================================
# ÉTATS DE SESSION
# ============================================================

if "used_indexes" not in st.session_state:
    st.session_state.used_indexes = []

if "current_index" not in st.session_state:
    st.session_state.current_index = None

if "reveal" not in st.session_state:
    st.session_state.reveal = False

if "game_started" not in st.session_state:
    st.session_state.game_started = False


# ============================================================
# FONCTIONS JEU
# ============================================================

def pick_new_quote():
    available_indexes = [
        i for i in df.index
        if i not in st.session_state.used_indexes
    ]

    if available_indexes:
        new_index = random.choice(available_indexes)

        st.session_state.current_index = new_index
        st.session_state.used_indexes.append(new_index)
        st.session_state.reveal = False
        st.session_state.game_started = True

    else:
        st.session_state.current_index = None


def reset_game():
    st.session_state.used_indexes = []
    st.session_state.current_index = None
    st.session_state.reveal = False
    st.session_state.game_started = False


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📌 Menu")

page = st.sidebar.radio(
    "Navigation",
    ["🎮 Jeu", "🗣️ Je balance", "📊 Stats"]
)

display_mode = st.sidebar.radio(
    "Mode d'affichage",
    ["🖥️ Mode PC", "📱 Mode mobile"]
)


# ============================================================
# ONGLET JEU
# ============================================================

if page == "🎮 Jeu":

    st.markdown('<div class="main-title">🎲 THE GAME</div>', unsafe_allow_html=True)

    total_quotes = len(df)
    used_quotes = len(st.session_state.used_indexes)
    remaining_quotes = total_quotes - used_quotes

    if not st.session_state.game_started:

        st.markdown(
            '<div class="subtitle">Le recueil des phrases cultes</div>',
            unsafe_allow_html=True
        )

        st.write(f"💬 **{total_quotes} citations** disponibles")
        st.write(f"👤 **{df['auteur'].nunique()} auteurs**")
        st.write(f"📢 **{df['denonciateur'].nunique()} dénonciateurs**")

        if st.button("▶️ Commencer la partie", use_container_width=True):
            pick_new_quote()
            st.rerun()

    else:

        st.caption(
            f"Progression : {used_quotes} / {total_quotes} citations vues"
        )

        st.progress(used_quotes / total_quotes)

        if st.session_state.current_index is not None:

            row = df.loc[st.session_state.current_index]

            st.markdown(
                f"""
                <div class="quote-card">
                    <div class="quote-text">“{row['citation']}”</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if not st.session_state.reveal:

                if st.button("👀 Révéler la réponse", use_container_width=True):
                    st.session_state.reveal = True
                    st.rerun()

            else:

                st.markdown('<div class="reveal-block">', unsafe_allow_html=True)

                if display_mode == "🖥️ Mode PC":

                    author_img_path = get_person_image_path(
                        row["auteur"],
                        AUT_IMG_DIR
                    )

                    den_img_path = get_person_image_path(
                        row["denonciateur"],
                        DEN_IMG_DIR
                    )

                    author_img = load_square_image(author_img_path, size=200)
                    den_img = load_square_image(den_img_path, size=200)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.image(author_img, width=200)

                        st.markdown(
                            f"""
                            <div class="person-label">
                                👤 Auteur : {row['auteur']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.image(den_img, width=200)

                        st.markdown(
                            f"""
                            <div class="person-label">
                                📢 Dénonciateur : {row['denonciateur']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                else:

                    st.markdown(
                        f"""
                        <div class="mobile-answer">
                            👤 Auteur : {row['auteur']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.markdown(
                        f"""
                        <div class="mobile-answer">
                            📢 Dénonciateur : {row['denonciateur']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"""
                    <div class="date-card">
                        📅 Date : {row['date_complete']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown('</div>', unsafe_allow_html=True)

                if remaining_quotes > 0:

                    if st.button("➡️ Citation suivante", use_container_width=True):
                        pick_new_quote()
                        st.rerun()

                else:
                    st.warning("Toutes les citations ont été jouées !")

        st.markdown("---")

        if st.button("🔄 Recommencer la partie", use_container_width=True):
            reset_game()
            st.rerun()


# ============================================================
# ONGLET JE BALANCE
# ============================================================

elif page == "🗣️ Je balance":

    st.title("🗣️ Je balance")

    st.write("Ajoute une nouvelle phrase directement dans le recueil.")

    denonciateurs = sorted(df["denonciateur"].dropna().unique().tolist())
    auteurs = sorted(df["auteur"].dropna().unique().tolist())

    denonciateur_choice = st.selectbox(
        "Moi,",
        denonciateurs + ["Autre"]
    )

    if denonciateur_choice == "Autre":
        denonciateur = st.text_input("Nouveau dénonciateur")
    else:
        denonciateur = denonciateur_choice

    auteur_choice = st.selectbox(
        "balance",
        auteurs + ["Autre"]
    )

    if auteur_choice == "Autre":
        auteur = st.text_input("Nouvel auteur")
    else:
        auteur = auteur_choice

    citation = st.text_area(
        "qui a dit",
        placeholder="Écris la citation ici..."
    )

    date_citation = st.date_input(
        "le",
        value=date.today(),
        format="DD/MM/YYYY"
    )

    if st.button("✅ Ajouter la citation", use_container_width=True):

        if not denonciateur or not auteur or not citation:
            st.error("Il manque au moins un champ : dénonciateur, auteur ou citation.")

        else:
            worksheet = get_worksheet()

            new_row = [
                date_citation.strftime("%Y-%m-%d"),
                "00:00:00",
                denonciateur.strip(),
                citation.strip(),
                auteur.strip(),
                date_citation.year
            ]

            worksheet.append_row(new_row)

            st.cache_data.clear()

            st.success("Citation ajoutée au recueil ✅")
            st.info("Elle sera disponible dans le jeu après actualisation ou nouvelle partie.")


# ============================================================
# ONGLET STATS
# ============================================================

elif page == "📊 Stats":

    st.title("📊 Statistiques")

    st.subheader("Auteurs les plus cités")

    st.bar_chart(
        df["auteur"]
        .value_counts()
        .sort_values(ascending=False)
        .head(10)
    )

    st.subheader("Dénonciateurs les plus actifs")

    st.bar_chart(
        df["denonciateur"]
        .value_counts()
        .sort_values(ascending=False)
        .head(10)
    )

    st.subheader("Citations par année")

    st.bar_chart(
        df["annee"]
        .value_counts()
        .sort_index()
    )