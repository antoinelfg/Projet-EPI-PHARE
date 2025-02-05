# 📊 Projet EPI-PHARE

Cette application **Streamlit** permet d’analyser des données épidémiologiques dans le cadre d'un projet entre les `Mines de Paris` et `EPI-PHARE`.

Elle permet :
- **Charger un fichier de données** (.xlsx ou .csv).
- **Explorer les caractéristiques des patients** (répartition géographique, admissions, traitements).
- **Visualiser la survie des patients** via des **courbes Kaplan-Meier**.
- **Analyser diverses métriques** sous forme de **graphiques interactifs**.

---

## 🚀 Installation et Exécution

### 1️⃣ Créer un compte Streamlit
L'application fonctionne avec **Streamlit**, et il est **nécessaire de créer un compte** pour l’utiliser en mode partagé sur le cloud.

📌 **Créer un compte gratuitement sur** 👉 [Streamlit Cloud](https://streamlit.io/cloud)

Vous pouvez ensuite **héberger** votre propre version de l’application ou la tester en local.

### 2️⃣ Cloner le dépôt

```bash
git clone https://github.com/antoinelfg/Projet-EPI-PHARE.git
cd Projet-EPI-PHARE
```

### 3️⃣ Installer les dépendances

Assurez-vous d’avoir Python 3.8+ installé, puis exécutez :

```bash
pip install -r requirements.txt
```

### 4️⃣ Lancer l’application Streamlit

```bash
streamlit run app.py
```

Cela ouvrira automatiquement l’interface interactive dans votre navigateur.

## 📂 Fichier de données requis

L’application nécessite un fichier de données au format .xlsx ou .csv pour fonctionner.

## 📌 Colonnes nécessaires :

Le fichier doit contenir au minimum les colonnes suivantes :

| Nom de la colonne     | Description |
|-----------------------|-------------|
| `mois_inclusion`      | Date d'inclusion du patient (format YYYY-MM) |
| `region`             | Région de résidence du patient |
| `etb_type`           | Type d'établissement médical |
| `indication`         | Indication du traitement |
| `top_deces`         | Statut de décès (1 = décédé, 0 = vivant) |
| `duree_ttt_mois`     | Durée du traitement en mois |
| `duree_survie_mois`  | Durée de survie après traitement en mois |

## 🛠️ Fonctionnalités principales

### 📂 Chargement et exploration des données
	•	Upload de fichiers Excel (.xlsx) et CSV.
	•	Nettoyage automatique des données.

### 📊 Analyses et visualisations
	•	Cartographie régionale du nombre de patients.
	•	Histogrammes interactifs pour explorer les types d’établissements.
	•	Courbes Kaplan-Meier pour analyser la survie des patients.
	•	Graphiques circulaires pour la répartition des métastases et des chirurgies.

## 🎯 Développement et Contributions

Si vous souhaitez modifier ou améliorer le projet :
	1.	Fork le dépôt.
	2.	Créer une branche (git checkout -b nouvelle-fonctionnalité).
	3.	Committer vos modifications (git commit -m "Ajout d'une analyse").
	4.	Pousser la branche (git push origin nouvelle-fonctionnalité).
	5.	Créer une Pull Request.
