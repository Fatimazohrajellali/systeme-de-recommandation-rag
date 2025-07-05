# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import plotly.express as px
from wordcloud import WordCloud

# Chemins des fichiers (modifie-les si besoin)
DRIVE_PATH = "/content/drive/MyDrive/rag_project"
INDEX_PATH = f"{DRIVE_PATH}/faiss_index.index"
DATA_PATH = "/content/drive/MyDrive/cleaned_articles.csv"

@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    texts = df["Contenu"].fillna("").tolist()
    metadata = df[["ID", "Titre", "URL"]].to_dict('records')
    index = faiss.read_index(INDEX_PATH)
    return df, texts, metadata, index

def search_articles(query, model, index, texts, metadata, top_k=5):
    query_embedding = model.encode([query])
    distances, indices = index.search(query_embedding, top_k)
    results = []
    for idx, score in zip(indices[0], distances[0]):
        if idx >= 0:
            result = metadata[idx].copy()
            result["score"] = float(1 - score)
            result["extrait"] = texts[idx][:200] + "..." if len(texts[idx]) > 200 else texts[idx]
            results.append(result)
    return sorted(results, key=lambda x: x["score"], reverse=True)

# Configuration de la page Streamlit
st.set_page_config(
    page_title="📚 Système de Recommandation RAG",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    :root {
        --primary: #4a6fa5;
        --secondary: #166088;
        --accent: #4cb944;
        --background: #f8f9fa;
        --card: #ffffff;
    }
    .main { background-color: var(--background); }
    .stTextInput input {
        border-radius: 20px;
        padding: 12px 20px;
        border: 2px solid #e0e0e0;
    }
    .stTextInput input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(74, 111, 165, 0.2);
    }
    .article-card {
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        background-color: var(--card);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .article-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }
    .score-badge {
        display: inline-block;
        padding: 6px 12px;
        border-radius: 16px;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        font-weight: bold;
        font-size: 14px;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50, #1a2639);
        color: white;
    }
    h1, h2, h3 { color: var(--secondary); }
    a {
        color: var(--primary);
        text-decoration: none;
    }
    a:hover {
        color: var(--secondary);
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar avec paramètres avancés
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/2c3e50/ffffff?text=RAG+System", width=150)
    st.title("⚙️ Paramètres Avancés")
    top_k = st.slider("Nombre de résultats", 3, 10, 5)
    min_score = st.slider("Score minimum", 0.0, 1.0, 0.3, step=0.05)
    st.markdown("---")
    st.markdown("""
    **✨ À propos**  
    Ce système utilise:
    - Modèle: all-MiniLM-L6-v2  
    - Index: FAISS  
    - Technique: RAG (Retrieval-Augmented Generation)
    """)

# En-tête et logo
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📚 Système de Recommandation RAG")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px;">
        <p style="font-size: 18px; color: #555;">
            Découvrez les articles les plus pertinents grâce à notre technologie avancée
        </p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.image("https://via.placeholder.com/100x100/4a6fa5/ffffff?text=AI", width=100)

# Zone de recherche
query = st.text_input("🔍 Recherche avancée", placeholder="Ex: Transformers, LSTM, NLP...")

if query:
    with st.spinner("🔎 Analyse en cours... Veuillez patienter"):
        model = load_model()
        df, texts, metadata, index = load_data()
        results = search_articles(query, model, index, texts, metadata, top_k=top_k)
        results = [r for r in results if r["score"] >= min_score]

    if results:
        # Affichage des métriques
        st.markdown("### 📊 Métriques")
        col1, col2, col3 = st.columns(3)
        col1.metric("Articles trouvés", len(results))
        col2.metric("Score moyen", f"{np.mean([r['score'] for r in results]):.2f}")
        col3.metric("Meilleur score", f"{max([r['score'] for r in results]):.2f}")

        # Articles recommandés (juste après les métriques)
        st.markdown(f"### 🗞️ Articles recommandés ({len(results)})")
        for i, res in enumerate(results, 1):
            with st.container():
                st.markdown(f"""
                <div class="article-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="color: var(--secondary); margin: 0;">{i}. {res['Titre']}</h3>
                        <div class="score-badge">Score: {res['score']:.2f}</div>
                    </div>
                    <p style="margin: 15px 0; color: #555; line-height: 1.6;">{res['extrait']}</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <a href="{res['URL']}" target="_blank" style="color: var(--primary); text-decoration: none; font-weight: 500;">
                            📖 Lire l'article complet
                        </a>
                        <small style="color: #888;">Longueur: {len(res['extrait'])} caractères</small>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Nuage de mots clés
        st.markdown("### 🌈 Nuage de mots clés")
        text_for_wordcloud = " ".join([res['Titre'] + " " + res['extrait'] for res in results])
        wordcloud = WordCloud(width=800, height=400, background_color='white', 
                              colormap='Blues', max_words=50).generate(text_for_wordcloud)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)

        # Analyse des scores
        st.markdown("### 📈 Analyse des scores")
        scores_df = pd.DataFrame({
            'Article': [f"Art. {i+1}" for i in range(len(results))],
            'Score': [res['score'] for res in results],
            'Titre': [res['Titre'][:40] + "..." for res in results],
            'URL': [res['URL'] for res in results]
        })
        fig = px.bar(scores_df, x='Article', y='Score', hover_data=['Titre'],
                     color='Score', color_continuous_scale='Teal',
                     height=400, width=800)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title=None,
            yaxis_title="Score de similarité",
            hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("Aucun résultat ne correspond à vos critères. Essayez d'élargir votre recherche.")

# Footer
st.markdown("""
<hr style="margin: 40px 0 20px; border: 0; height: 1px; background: linear-gradient(90deg, transparent, var(--primary), transparent);">
<div style="text-align: center; color: #777; font-size: 14px; padding: 20px 0;">
    <p>Système de Recommandation RAG - © 2025 | Version 2.0</p>
    <p style="font-size: 12px; margin-top: 5px;">Technologies: Streamlit, Sentence Transformers, FAISS</p>
</div>
""", unsafe_allow_html=True)
