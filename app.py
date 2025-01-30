import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from lifelines import KaplanMeierFitter
from plotly.subplots import make_subplots
import json
import requests
from streamlit_plotly_events import plotly_events
import numpy as np

st.set_page_config(layout="wide")


st.sidebar.title("📂 Charger un fichier")

# File uploader widget
uploaded_file = st.sidebar.file_uploader("Téléverser un fichier (.xlsx ou .csv)", type=["xlsx", "csv"])

# Load dataset
if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1]  # Get file extension
    
    if file_extension == "xlsx":
        df = pd.read_excel(uploaded_file)
    elif file_extension == "csv":
        df = pd.read_csv(uploaded_file)
    
    st.sidebar.success(f"✅ Fichier chargé : {uploaded_file.name}")

else:
    df = pd.read_excel('base_anonyme_tdxd.xlsx')  # Default dataset
    st.sidebar.info("📌 Aucun fichier chargé. Utilisation du dataset par défaut.")

# Toggle for showing data preview
show_data = st.sidebar.checkbox("Afficher l'aperçu des données", value=False)

# Display dataset preview if checkbox is selected
if show_data:
    st.subheader("📊 Aperçu des données")
    st.write(df.head())


logo_path = "/Users/fork/Documents/Mines/3A/EpiPhare/logo_epi.png"  # Replace with the actual path

# --- Sidebar: Editable Metadata ---
st.sidebar.header("📝 Modifier les informations")

# Editable fields for metadata in sidebar
author = st.sidebar.text_input("Auteur(s)", "Nom de l’auteur")
date = st.sidebar.date_input("Date de l’étude")
project_name = st.sidebar.text_input("Nom du projet", "Analyse de ...")

# --- Main Content: Logo & Metadata Display ---
col1, col2 = st.columns([2, 1])  # Adjust layout size

with col2:
    st.write('\n')
    st.write('\n')
    st.image(logo_path, width=300)  # Adjust size if needed

with col1:
    st.title("Étude Épidémiologique")
    st.write(f"📅 **Date :** {date}")
    st.write(f"✍️ **Auteur(s) :** {author}")
    st.write(f"📌 **Projet :** {project_name}")

def clean_dataframe(df):
    for col in df.columns:
        # Check if the column is of object type (e.g., strings)
        if df[col].dtype == "object":
            # Replace 'Missing' or other placeholders with NaN
            df[col] = df[col].replace(["Missing", "N/A", "None"], np.nan)
        # Try converting to numeric where possible
        try:
            df[col] = pd.to_numeric(df[col])
        except ValueError:
            pass  # Keep as is if conversion fails
    return df

# Apply cleaning function
df = clean_dataframe(df)

# Ensure the `mois_inclusion` column is in datetime format
df['mois_inclusion'] = pd.to_datetime(df['mois_inclusion'])

# Map the `indication` column to determine the group
df['group'] = df['indication'].map({
    'CDERU01': 'HER2+ 3L+',
    'CDERU02': 'HER2+ 2L+',
    'CDERU04': 'HER2-low 2L+'
})

df['top_deces'] = df['top_deces'].astype(int)  # Statut de décès

# Default text for editable sections
default_title = "Analyse Épidémiologique - EPI-PHARE"
default_intro = (
    "Cette étude s’intéresse à l’utilisation d’un médicament appelé trastuzumab deruxtecan (T-DXd) "
    "pour traiter des formes avancées de cancer du sein en France. Elle examine deux groupes de patients : "
    "ceux atteints d’un cancer HER2-positif (une forme liée à une protéine spécifique) et ceux avec des "
    "niveaux plus faibles de cette protéine (HER2-low)."
)
default_conclusion = (
    "L’étude montre que le trastuzumab deruxtecan est utilisé avec succès chez des patients plus âgés et "
    "présentant des conditions médicales complexes, comparé à ceux des essais cliniques. Bien qu’il améliore "
    "les résultats pour de nombreux patients, il peut également entraîner des effets secondaires nécessitant "
    "des hospitalisations."
)

# Sidebar for text modification
st.sidebar.title("Modify Text Sections")
title = st.sidebar.text_input("Title:", default_title)
introduction = st.sidebar.text_area("Introduction:", default_intro)
conclusion = st.sidebar.text_area("Conclusion:", default_conclusion)

# Sidebar for Section Selection
st.sidebar.title("Navigation")
sections = st.sidebar.multiselect(
    "Choose sections to display:",
    options=["Introduction", "Région", "Admissions Over Time", "Survie", "Répartition des Métastases et Chirurgies", "Conclusion"],
    default=["Introduction", "Région", "Admissions Over Time", "Survie", "Répartition des Métastases et Chirurgies", "Conclusion"]
)

# Main title
st.title(title)


def plot_individual_kaplan_meier(data, time_col, event_col, title_prefix):
    groups = data['group'].unique()
    colors = ["#1F4E79", "#4682B4", "#87CEEB"]  # Blue Shades Palette

    # Create columns for the 3 groups
    col1, col2, col3 = st.columns(3)
    for i, (col, group) in enumerate(zip([col1, col2, col3], groups)):
        with col:
            #st.write(f"{title_prefix} pour le groupe {group}")

            # Filter data for the group
            group_data = data[data['group'] == group]
            kmf = KaplanMeierFitter()
            kmf.fit(
                group_data[time_col],  # Time column (e.g., `duree_ttt_mois` or `duree_survie_mois`)
                event_observed=group_data[event_col],  # Event column (e.g., `top_deces`)
                label=group
            )

            # Calculate survival data
            survival_function = kmf.survival_function_
            at_risk_counts = kmf.event_table['at_risk']

            # Median survival
            median_survival = kmf.median_survival_time_
            survival_at_median = survival_function.loc[survival_function.index <= median_survival].iloc[-1, 0]

            # Create Plotly figure
            fig = go.Figure()

            # Add the survival curve
            fig.add_trace(
                go.Scatter(
                    x=survival_function.index,
                    y=survival_function.iloc[:, 0],
                    mode='lines',  # Line for survival curve
                    name="Survival Curve",
                    line=dict(color=colors[i], width=3),
                    hoverinfo="skip"  # Disable hovering for the line itself
                )
            )

            # Add monthly markers with hover data
            monthly_indices = survival_function.index[
                survival_function.index.astype(int) % 1 == 0
            ]  # Keep only integer months
            fig.add_trace(
                go.Scatter(
                    x=monthly_indices,
                    y=survival_function.loc[monthly_indices].iloc[:, 0],
                    mode='markers',  # Add markers
                    name="Monthly Points",
                    marker=dict(color=colors[i], size=8, symbol='circle'),
                    customdata=at_risk_counts.loc[monthly_indices],  # Add subjects at risk as custom data
                    hovertemplate=(
                        "<b>Month: %{x:.0f}</b><br>"
                        "Survival Probability: %{y:.2%}<br>"
                        "Subjects at Risk: %{customdata}<extra></extra>"
                    )
                )
            )

            # Add a horizontal line for the median survival
            fig.add_trace(
                go.Scatter(
                    x=[0, max(survival_function.index)],  # Extend horizontally
                    y=[survival_at_median, survival_at_median],
                    mode="lines",
                    name="Median Survival",
                    line=dict(color="red", dash="dash"),
                    hovertemplate=f"<b>Median Survival: {median_survival:.2f} months<br>Survival: {survival_at_median:.2%}</b><extra></extra>"
                )
            )

            # Update layout for the graph
            fig.update_layout(
                title=dict(
                    text=f"{title_prefix} ({group})",
                    x=0.20,
                    font=dict(size=16)
                ),
                xaxis=dict(
                    title="Time (Months)",
                    tickfont=dict(size=12),
                    titlefont=dict(size=14),
                    showgrid=True,
                    gridcolor="rgba(200, 200, 200, 0.4)"
                ),
                yaxis=dict(
                    title="Survival Probability",
                    tickfont=dict(size=12),
                    titlefont=dict(size=14),
                    showgrid=True,
                    gridcolor="rgba(200, 200, 200, 0.4)"
                ),
                height=400,
                width=400,
                legend=dict(font=dict(size=10))
            )

            # Display the graph
            st.plotly_chart(fig)


# Introduction Section
if "Introduction" in sections:
    st.subheader("Introduction")
    st.write(introduction)


if "Survie" in sections:
    st.subheader("Kaplan-Meier: Survie sans progression")
    st.write("Courbes Kaplan-Meier séparées montrant les points mensuels avec le pourcentage de survie et le nombre de sujets à risque, ainsi qu'une ligne horizontale pour la médiane de survie.")
    plot_individual_kaplan_meier(df, time_col='duree_ttt_mois', event_col='top_deces', title_prefix="Survie sans progression")

    ### Overall Survival
    st.subheader("Kaplan-Meier: Survie globale")
    st.write("Courbes Kaplan-Meier séparées montrant les points mensuels avec le pourcentage de survie et le nombre de sujets à risque, ainsi qu'une ligne horizontale pour la médiane de survie.")
    plot_individual_kaplan_meier(df, time_col='duree_survie_mois', event_col='top_deces', title_prefix="Survie globale")

if 'Région' in sections:
    st.sidebar.header("Filtres")
    selected_region = st.sidebar.selectbox("Sélectionner une région", options=df["region"].unique(), index=0)
    selected_etablissement = st.sidebar.selectbox("Sélectionner un type d’établissement", options=df["etb_type"].unique(), index=0)
    selected_indication = st.sidebar.selectbox("Sélectionner une indication", options=df["indication"].unique(), index=0)

    # Filter dataset based on selections
    filtered_df = df[
        (df["region"] == selected_region) &
        (df["etb_type"] == selected_etablissement) &
        (df["indication"] == selected_indication)
    ]

    # Ensure correct data types
    df["region"] = df["region"].astype(str).str.strip().str.lower()

    # Load France's GeoJSON for regions
    geojson_url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/regions.geojson"
    geojson_data = requests.get(geojson_url).json()

    # Aggregate patient count by region
    region_counts = df["region"].value_counts().reset_index()
    region_counts.columns = ["region", "patients"]

    df["region"] = df["region"].astype(str).str.strip().str.lower()

    # Replace incorrect names with the correct region mapping
    region_mapping = {
        "ile-de-france": "Île-de-France",
        "hauts-de-france": "Hauts-de-France",
        "bourgogne-franche-comté": "Bourgogne-Franche-Comté",
        "nouvelle-aquitaine": "Nouvelle-Aquitaine",
        "occitanie": "Occitanie",
        "bretagne": "Bretagne",
        "provence-alpes-côte d'azur": "Provence-Alpes-Côte d'Azur",
        "auvergne-rhône-alpes": "Auvergne-Rhône-Alpes",
        "grand est": "Grand Est",
        "centre-val-de-loire": "Centre-Val de Loire",
        "pays de la loire": "Pays de la Loire",
        "normandie": "Normandie",
        "corse": "Corse",
        "dom": "Guadeloupe",  # Assign one region (adjust if needed)
        "nan": None  # Convert NaN values to None
    }

    df["region"] = df["region"].replace(region_mapping)

    region_counts["region"] = region_counts["region"].replace(region_mapping)

    # Initialize session state for selected region
    if "selected_region" not in st.session_state:
        st.session_state.selected_region = None

    st.title("Analyse Régionale et Hospitalière")

    # Layout with two columns
    col1, col2 = st.columns(2)

    ### 1. Regional Histogram ###
    with col1:
        st.subheader("Histogramme des patients par région")
        fig_region_hist = px.bar(
            region_counts,
            x="region",
            y="patients",
            title="Répartition des patients par région",
            labels={"patients": "Nombre de patients", "region": "Région"},
            color="patients",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_region_hist, use_container_width=True)

    ### 2. Clickable Regional Map ###
    with col2:
        st.subheader("Carte des patients par région")

        fig_region_map = px.choropleth(
            region_counts,
            geojson=geojson_data,
            locations="region",
            featureidkey="properties.nom",
            color="patients",
            color_continuous_scale="Blues",
            title="Nombre de patients par région en France",
            labels={"patients": "Nombre de patients"},
        )

        fig_region_map.update_geos(
            visible=False,
            showcountries=False,
            bgcolor="rgba(0,0,0,0)",
            fitbounds="locations",
            scope="europe",
            projection_scale=6.5
        )

        fig_region_map.update_layout(
            title_x=0.5,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            dragmode=False
        )

        # Capture click event
        selected_region_event = plotly_events(fig_region_map, click_event=True)

        # Extract region name from pointIndex
        if selected_region_event and isinstance(selected_region_event, list) and len(selected_region_event) > 0:
            point_index = selected_region_event[0].get("pointIndex")
            if point_index is not None:
                selected_region_name = region_counts.iloc[point_index]["region"]
                st.session_state.selected_region = selected_region_name

    # Display the selected region
    st.write("Selected Region in Session State:", st.session_state.selected_region)
    # Filter dataset based on selected region
    if st.session_state.selected_region:
        selected_region = st.session_state.selected_region.lower().strip()
        filtered_df = df[df["region"] == selected_region]

    else:
        filtered_df = df  # Show all data if no selection
    # Reset selection button
    if st.session_state.selected_region:
        st.markdown(f"### Région sélectionnée : **{st.session_state.selected_region}**")
        if st.button("Réinitialiser"):
            st.session_state.selected_region = None

    # Filter dataset based on selected region
    if st.session_state.selected_region:
        filtered_df = df[df["region"] == st.session_state.selected_region]
        if filtered_df.empty:
            st.warning("⚠️ Aucun patient trouvé pour cette région.")
    else:
        filtered_df = df  # Show all data if no selection

        ### 3 & 4. Quintile de Défavourisation & Type d'Établissement (Side by Side) ###
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Répartition selon le Quintile de Défavourisation")

        # Prepare data
        quintile_counts = filtered_df["quintile_defav"].value_counts().reset_index()
        quintile_counts.columns = ["Quintile", "Count"]

        # Define a blue shades color palette
        blue_shades = ["#1F4E79", "#4682B4", "#87CEEB", "#5F9EA0", "#B0E0E6"]  # Dark to Light Blue

        # Create the pie chart with blue shades
        fig_quintile = go.Figure(go.Pie(
            labels=quintile_counts["Quintile"],
            values=quintile_counts["Count"],
            textinfo="percent+label",
            marker=dict(colors=blue_shades)  # Apply blue shades
        ))

        st.plotly_chart(fig_quintile)

    with col2:
        st.subheader("Répartition par Type d'Établissement")
        etablissement_counts = filtered_df["etb_type"].value_counts().reset_index()
        etablissement_counts.columns = ["Type", "Count"]
        fig_etab = px.bar(
            etablissement_counts,
            x="Type",
            y="Count",
            title="Nombre de patients par type d’établissement",
            labels={"Type": "Type d'établissement", "Count": "Nombre de patients"},
            color="Count",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_etab)

    ### 4. Number of Initiations Over Time Line Chart ###
    st.subheader("Nombre d’initiations par mois / année")
    initiations_over_time = filtered_df.groupby(filtered_df["mois_inclusion"].dt.to_period("M")).size().reset_index(name="Count")
    initiations_over_time["mois_inclusion"] = initiations_over_time["mois_inclusion"].dt.to_timestamp()
    fig_initiations = px.line(
        initiations_over_time,
        x="mois_inclusion",
        y="Count",
        title="Nombre d’initiations par mois",
        labels={"mois_inclusion": "Date", "Count": "Nombre d’initiations"},
        markers=True
    )
    st.plotly_chart(fig_initiations)

# Admissions Over Time Section in the first column
if "Admissions Over Time" in sections:
    st.subheader("Admissions par Groupe")
    st.write(
            """
            Courbes montrant l’évolution du nombre d’admissions de patients selon les groupes.
            """)
        # Group by month and group type, then count the number of patients
    grouped_data = (
            df.groupby([df['mois_inclusion'].dt.to_period('M'), 'group'])
            .size()
            .reset_index(name='Number of Patients')
        )
    grouped_data['mois_inclusion'] = grouped_data['mois_inclusion'].dt.to_timestamp()

        # Create an interactive line chart with Plotly
    fig = px.line(
            grouped_data,
            x='mois_inclusion',
            y='Number of Patients',
            color='group',
            title='Number of Patients Admitted Over Time by Group',
            labels={
                'mois_inclusion': 'Date',
                'Number of Patients': 'Admissions',
                'group': 'Group'
            },
            markers=True,
        )

        # Update layout for improved aesthetics and center the title
    fig.update_layout(
            title=dict(
                text="Number of Patients Admitted Over Time by Group",
                xanchor="center",
                x=0.5,  # Center the title
                font=dict(size=18),
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',  # Light gridlines
                title_text="Date"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',  # Light gridlines
                title_text="Number of Patients"
            ),
            legend_title="Group",
            height=600,
            width=900
        )

        # Render the interactive plot
    st.plotly_chart(fig)


# Add a new subsection with a catchphrase
if "Répartition des Métastases et Chirurgies" in sections:
    st.subheader("Répartition des Métastases et Chirurgies")
    st.write("Un aperçu visuel de la répartition des métastases et des types de chirurgies chez les patients.")

    # Filter the data for metastases
    metastase_df = df[df['top_meta'] == 1]
    metastase_columns = [
        'top_meta_gang', 'top_meta_os', 'top_meta_dig',
        'top_meta_poum', 'top_meta_brain'
    ]
    metastase_counts = metastase_df[metastase_columns].sum().reset_index()
    metastase_counts.columns = ['Type de métastase', 'Nombre']

    # Filter the data for surgeries
    chirurgie_df = df[df['top_chir'] == 1]
    chirurgie_columns = [
        'top_radio', 'top_hormono', 'top_tdm1', 'top_trastu_pertu',
        'top_trastu', 'top_tki_her2', 'top_chimio_peros', 'top_cdk46',
        'top_pdl1', 'top_parpi', 'top_sac_gov'
    ]
    chirurgie_counts = chirurgie_df[chirurgie_columns].sum().reset_index()
    chirurgie_counts.columns = ['Type de chirurgie', 'Nombre']

    # Create the pie chart for metastases
    fig_metastase = go.Pie(
        labels=metastase_counts['Type de métastase'],
        values=metastase_counts['Nombre'],
        textinfo='percent+label',  # Labels and percentages in the pie chart
        hole=0.4,  # Donut style
        pull=[0.1 if i == metastase_counts['Nombre'].idxmax() else 0 for i in range(len(metastase_counts))],
        marker=dict(colors=px.colors.sequential.Sunset)  # Sunset color palette
    )

    # Create the pie chart for surgeries
    fig_chirurgie = go.Pie(
        labels=chirurgie_counts['Type de chirurgie'],
        values=chirurgie_counts['Nombre'],
        textinfo='percent+label',  # Labels and percentages in the pie chart
        hole=0.4,  # Donut style
        pull=[0.1 if i == chirurgie_counts['Nombre'].idxmax() else 0 for i in range(len(chirurgie_counts))],
        marker=dict(colors=px.colors.sequential.Aggrnyl)  # Aggrnyl color palette
    )

    # Create side-by-side subplots
    fig = make_subplots(
        rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'domain'}]],
        subplot_titles=("Métastases", "Chirurgies")
    )

    # Add the two pie charts to the subplots
    fig.add_trace(fig_metastase, row=1, col=1)
    fig.add_trace(fig_chirurgie, row=1, col=2)

    # Adjust the layout
    fig.update_layout(
        title_text="Répartition des Métastases et Chirurgies",
        title_x=0.35,
        height=600,  # Height of the figure
        width=1000,  # Width of the figure
        margin=dict(t=70, b=0, l=0, r=0),  # Adjust margins
        showlegend=False  # Remove the external legend
    )

    # Display the interactive plot in Streamlit
    st.plotly_chart(fig)

# Conclusion Section
if "Conclusion" in sections:
    st.subheader("Conclusion")
    st.write(conclusion)
