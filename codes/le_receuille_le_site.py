import streamlit as st
from pathlib import Path
from PIL import Image
import pandas as pd
import random
import gspread
import altair as alt
import re
from google.oauth2.service_account import Credentials
from datetime import date, datetime
from zoneinfo import ZoneInfo

# ============================================================
# CONFIG PAGE
# ============================================================

st.set_page_config(
    page_title="THE GAME",
    page_icon="🎲",
    layout="centered"
)

# ============================================================
# STYLE CSS
# ============================================================

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

.quote-card, .date-card, .mobile-answer, .balance-card, .preview-card, .id-card, .stat-card {
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.25);
}

.quote-card {
    padding: 32px;
    margin: 25px 0;
    text-align: center;
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
    padding: 14px;
    margin: 10px 0;
    text-align: center;
    font-size: 18px;
    font-weight: 700;
}

.date-card {
    padding: 12px;
    margin: 20px 0;
    text-align: center;
    font-size: 22px;
    font-weight: 800;
}

.balance-card {
    padding: 24px;
    margin: 20px 0;
}

.preview-card {
    padding: 20px;
    margin: 20px 0;
    text-align: center;
}

.preview-quote {
    font-size: 24px;
    font-weight: 800;
    line-height: 1.35;
}

.id-card {
    padding: 24px;
    margin: 20px 0;
}

.author-name {
    text-align: center;
    font-size: 42px;
    font-weight: 900;
    margin-bottom: 10px;
}

.first-quote-label {
    text-align: center;
    font-size: 18px;
    font-weight: 700;
    opacity: 0.8;
}

.first-quote-text {
    text-align: center;
    font-size: 24px;
    font-weight: 800;
    line-height: 1.35;
    margin-top: 12px;
}

.first-quote-date {
    text-align: center;
    font-size: 16px;
    opacity: 0.75;
    margin-top: 10px;
}

.stat-card {
    padding: 18px;
    text-align: center;
    margin: 8px 0;
    min-height: 105px;
}

.stat-value {
    font-size: 20px;
    font-weight: 900;
    line-height: 1.2;
    word-break: break-word;
}

.stat-label {
    font-size: 14px;
    opacity: 0.75;
    margin-bottom: 8px;
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
# OUTILS STATS
# ============================================================

def make_bar_chart(data, x_col, y_col, title=None):
    chart_height = max(320, len(data) * 35)

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{x_col}:Q", title=None),
            y=alt.Y(
                f"{y_col}:N",
                sort="-x",
                title=None,
                axis=alt.Axis(labelLimit=220, labelFontSize=12)
            ),
            tooltip=[y_col, x_col]
        )
        .properties(height=chart_height, title=title)
    )

    st.altair_chart(chart, use_container_width=True)


def make_year_chart(data, year_col="annee", count_col="nb", title=None):
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{year_col}:O", title="Année", sort=None),
            y=alt.Y(f"{count_col}:Q", title="Nombre de citations"),
            tooltip=[year_col, count_col]
        )
        .properties(height=280, title=title)
    )

    st.altair_chart(chart, use_container_width=True)


def get_top_words(texts, limit=15):
    stopwords = {
        "je", "j", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
        "le", "la", "les", "un", "une", "des", "du", "de", "d", "au", "aux",
        "et", "ou", "mais", "donc", "or", "ni", "car",
        "ce", "ces", "cet", "cette", "ça", "ca", "c",
        "est", "suis", "es", "sont", "etre", "être",
        "a", "à", "ai", "as", "ont", "avoir",
        "que", "qui", "quoi", "dont", "où", "pour", "par", "avec", "sans",
        "dans", "sur", "sous", "en", "y",
        "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses",
        "moi", "toi", "lui", "leur", "leurs",
        "pas", "plus", "moins", "très", "tres", "bien",
        "ne", "n", "me", "te", "se", "m", "t", "s", "l",
        "cest", "c'est", "jai", "j'ai", "peut", "peux", "peu",
        "fait", "faire", "faut", "vais", "veux", "veut",
        "dire", "dit", "quand", "comme", "alors", "tout",
        "tous", "toute", "toutes", "bah", "hein", "genre",
        "non", "oui", "bon", "ben", "bah", "voilà", "voila",
        "là", "la", "ici", "même", "meme", "juste",
        "être", "etre", "avoir", "aller", "va", "vas",
        "ça", "ca", "cest", "c'est", "qu", "quand",
        "si", "du", "des", "dans", "parce", "parceque", "aussi",
        "alors", "donc", "mais", "ou", "ni", "car", "qu'il", "qu'elle", "qu'ils", "qu'elles",
        "sais", "sait", "savent", "savoir", "veux", "veut", "vont", "vais",
        "faut", "falloir", "peut", "peux", "peuvent", "peut-être", "peutetre", "peutetre", "peut-etre","fais", 
        "fait", "font", "faire", "dis", "dit", "disent", "dire","j'en", "y'a", 
        "quelqu'un", "quelqu'une", "quelqu'unes", "quelqu'uns", "quelques", "quelque", "quelqu'","c'était",
        "était", "étaient", "étant", "étée", "étées", "étés", "être", "tant", "l'ai", "l'as", "l'ont",
        "l'avons", "l'avez", "l'ont", "l'a", "l'as", "l'ont", "l'avons", "l'avez",
    }

    words = []

    for text in texts.dropna():
        clean_text = str(text).lower()

        clean_text = clean_text.replace("j’ai", "jai")
        clean_text = clean_text.replace("j'ai", "jai")
        clean_text = clean_text.replace("c’est", "cest")
        clean_text = clean_text.replace("c'est", "cest")
        clean_text = clean_text.replace("qu’il", "quil")
        clean_text = clean_text.replace("qu'elle", "quelle")
        clean_text = clean_text.replace("qu’elle", "quelle")

        clean_text = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ\s'-]", " ", clean_text)

        for word in clean_text.split():
            word = word.strip("'- ")

            if len(word) >= 3 and word not in stopwords:
                words.append(word)

    if not words:
        return pd.DataFrame(columns=["mot", "nb"])

    top_words = (
        pd.Series(words)
        .value_counts()
        .head(limit)
        .reset_index()
    )

    top_words.columns = ["mot", "nb"]

    return top_words


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
    ["🎮 Jeu", "🗣️ Je balance", "📚 Recueil", "📊 Stats"]
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

    st.title("🗣️ Je balance une phrase")

    st.write("Ajoute une nouvelle citation directement dans le recueil.")

    st.markdown('<div class="balance-card">', unsafe_allow_html=True)

    denonciateurs = sorted(df["denonciateur"].dropna().unique().tolist())
    auteurs = sorted(df["auteur"].dropna().unique().tolist())

    st.markdown("### Moi,")

    denonciateur_choice = st.selectbox(
        "Dénonciateur",
        denonciateurs + ["Autre"],
        label_visibility="collapsed"
    )

    if denonciateur_choice == "Autre":
        denonciateur = st.text_input(
            "Nouveau dénonciateur",
            placeholder="Entre le nom du dénonciateur"
        )
    else:
        denonciateur = denonciateur_choice

    st.markdown("### balance")

    auteur_choice = st.selectbox(
        "Auteur",
        auteurs + ["Autre"],
        label_visibility="collapsed"
    )

    if auteur_choice == "Autre":
        auteur = st.text_input(
            "Nouvel auteur",
            placeholder="Entre le nom de l'auteur"
        )
    else:
        auteur = auteur_choice

    st.markdown("### qui a dit :")

    citation = st.text_area(
        "Citation",
        placeholder="Écris la citation ici...",
        label_visibility="collapsed"
    )

    st.markdown("### le")

    date_citation = st.date_input(
        "Date de la citation",
        value=date.today(),
        format="DD/MM/YYYY",
        label_visibility="collapsed"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if denonciateur and auteur and citation:
        st.markdown(
            f"""
            <div class="preview-card">
                <div>
                    <strong>{denonciateur}</strong> balance <strong>{auteur}</strong>
                </div>
                <br>
                <div class="preview-quote">
                    “{citation}”
                </div>
                <br>
                <div>
                    le {date_citation.strftime("%d/%m/%Y")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("✅ Balancer la phrase", use_container_width=True):

        if not denonciateur or not auteur or not citation:
            st.error("Il manque au moins un champ : dénonciateur, auteur ou citation.")

        else:
            worksheet = get_worksheet()

            heure_ajout = datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M:%S")

            new_row = [
                date_citation.strftime("%Y-%m-%d"),
                heure_ajout,
                denonciateur.strip(),
                citation.strip(),
                auteur.strip(),
                date_citation.year
            ]

            worksheet.append_row(new_row)

            st.cache_data.clear()

            st.success("Phrase balancée dans le recueil ✅")
            st.info("Elle est maintenant disponible dans le jeu.")


# ============================================================
# ONGLET RECUEIL
# ============================================================

elif page == "📚 Recueil":

    st.title("📚 Recueil complet")

    st.write("Consulte toutes les citations du recueil.")

    filtered_df = df.copy()

    auteurs = sorted(filtered_df["auteur"].dropna().unique().tolist())
    denonciateurs = sorted(filtered_df["denonciateur"].dropna().unique().tolist())
    annees = sorted(filtered_df["annee"].dropna().astype(str).unique().tolist())

    col_filter1, col_filter2, col_filter3 = st.columns(3)

    with col_filter1:
        selected_auteurs = st.multiselect(
            "Auteurs",
            auteurs
        )

    with col_filter2:
        selected_denonciateurs = st.multiselect(
            "Dénonciateurs",
            denonciateurs
        )

    with col_filter3:
        selected_annees = st.multiselect(
            "Années",
            annees
        )

    if selected_auteurs:
        filtered_df = filtered_df[filtered_df["auteur"].isin(selected_auteurs)]

    if selected_denonciateurs:
        filtered_df = filtered_df[filtered_df["denonciateur"].isin(selected_denonciateurs)]

    if selected_annees:
        filtered_df = filtered_df[filtered_df["annee"].astype(str).isin(selected_annees)]

    st.caption(f"{len(filtered_df)} citation(s) affichée(s)")

    recueil_table = (
        filtered_df[["citation", "auteur", "denonciateur", "date_complete"]]
        .rename(columns={
            "citation": "Citation",
            "auteur": "Auteur",
            "denonciateur": "Dénonciateur",
            "date_complete": "Date"
        })
    )

    st.dataframe(
        recueil_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ONGLET STATS
# ============================================================

elif page == "📊 Stats":

    st.title("📊 Archives du Recueil")

    stats_view = st.radio(
        "Choisis une vue",
        ["🌍 Vue globale", "🪪 Fiche auteur"],
        horizontal=True
    )

    if stats_view == "🌍 Vue globale":

        st.subheader("🌍 Vue globale du recueil")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💬 Citations", len(df))

        with col2:
            st.metric("👤 Auteurs", df["auteur"].nunique())

        with col3:
            st.metric("📢 Dénonciateurs", df["denonciateur"].nunique())

        st.markdown("---")

        top_auteurs = (
            df["auteur"]
            .value_counts()
            .reset_index()
        )
        top_auteurs.columns = ["auteur", "nb"]

        top_denonciateurs = (
            df["denonciateur"]
            .value_counts()
            .reset_index()
        )
        top_denonciateurs.columns = ["denonciateur", "nb"]

        citations_par_annee = (
            df["annee"]
            .value_counts()
            .reset_index()
        )
        citations_par_annee.columns = ["annee", "nb"]
        citations_par_annee["annee"] = citations_par_annee["annee"].astype(str)
        citations_par_annee = citations_par_annee.sort_values("annee")

        make_bar_chart(
            top_auteurs.head(15),
            x_col="nb",
            y_col="auteur",
            title="Top auteurs"
        )

        make_bar_chart(
            top_denonciateurs.head(15),
            x_col="nb",
            y_col="denonciateur",
            title="Top dénonciateurs"
        )

        make_year_chart(
            citations_par_annee,
            year_col="annee",
            count_col="nb",
            title="Citations par année"
        )

    else:

        auteurs = sorted(df["auteur"].dropna().unique().tolist())

        selected_author = st.selectbox(
            "Choisis un auteur",
            auteurs
        )

        author_df = df[df["auteur"] == selected_author].copy()
        author_df = author_df.sort_values("date_message")

        first_row = author_df.iloc[0]
        last_row = author_df.iloc[-1]

        author_img_path = get_person_image_path(selected_author, AUT_IMG_DIR)
        author_img = load_square_image(author_img_path, size=180)

        st.markdown('<div class="id-card">', unsafe_allow_html=True)

        col_photo, col_infos = st.columns([1, 2])

        with col_photo:
            st.image(author_img, width=180)

        with col_infos:
            st.markdown(
                f"""
                <div class="author-name">{selected_author}</div>
                <div class="first-quote-label">
                    Et voilà comment je suis arrivé là :
                </div>
                <div class="first-quote-text">
                    “{first_row['citation']}”
                </div>
                <div class="first-quote-date">
                    {first_row['date_complete']}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        main_denonciateur = (
            author_df["denonciateur"].value_counts().idxmax()
            if len(author_df) > 0
            else "—"
        )

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        with kpi1:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-label">💬 Citations</div>
                    <div class="stat-value">{len(author_df)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi2:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-label">📢 Dénonciateurs</div>
                    <div class="stat-value">{author_df['denonciateur'].nunique()}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi3:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-label">🕵️ Balanceur principal</div>
                    <div class="stat-value">{main_denonciateur}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with kpi4:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-label">📅 Dernière apparition</div>
                    <div class="stat-value">{last_row['date_complete']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")

        graph1, graph2 = st.columns(2)

        with graph1:
            top_den_for_author = (
                author_df["denonciateur"]
                .value_counts()
                .reset_index()
            )
            top_den_for_author.columns = ["denonciateur", "nb"]

            make_bar_chart(
                top_den_for_author.head(10),
                x_col="nb",
                y_col="denonciateur",
                title="Qui me balance le plus ?"
            )

        with graph2:
            author_by_year = (
                author_df["annee"]
                .value_counts()
                .reset_index()
            )
            author_by_year.columns = ["annee", "nb"]
            author_by_year["annee"] = author_by_year["annee"].astype(str)
            author_by_year = author_by_year.sort_values("annee")

            make_year_chart(
                author_by_year,
                year_col="annee",
                count_col="nb",
                title="Mes citations par année"
            )

        graph3, graph4 = st.columns(2)

        with graph3:
            top_words = get_top_words(author_df["citation"], limit=15)

            if len(top_words) > 0:
                make_bar_chart(
                    top_words,
                    x_col="nb",
                    y_col="mot",
                    title="Mes mots les plus fréquents"
                )
            else:
                st.info("Pas assez de texte pour afficher les mots fréquents.")

        with graph4:
            st.subheader("Toutes mes citations")
            st.dataframe(
                author_df[["citation", "date_complete", "denonciateur"]]
                .rename(columns={
                    "citation": "Citation",
                    "date_complete": "Date",
                    "denonciateur": "Dénonciateur"
                }),
                use_container_width=True,
                hide_index=True
            )