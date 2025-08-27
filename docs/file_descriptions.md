# Documentation des Fichiers Python

Ce document décrit brièvement le rôle et le fonctionnement de chaque fichier Python dans le projet.

## ui/ui.py
Gère l'interface utilisateur en utilisant Streamlit. Configure la page, gère les projets et sessions des utilisateurs, fournit des fonctionnalités pour le téléversement de fichiers, et gère l'état du chat.

## app/settings.py
Gère les paramètres de configuration de l'application en utilisant Pydantic pour valider et charger les variables d'environnement, telles que les clés API et les URL de service.

## app/retriever.py
Module pour la récupération de documents en utilisant les services OpenAI et Qdrant. Il calcule les embeddings pour les requêtes et les passages de texte, et cherche les passages pertinents via Qdrant.

## app/memory.py
Gère la mémoire des sessions utilisateurs, utilisant Zep pour stocker et récupérer les messages du chat dans une session donnée pour fournir du contexte.

## app/main.py
Point d'entrée principal de l'application, utilisant FastAPI pour définir des endpoints d'API pour gérer les projets, interagir avec le chat, et ingérer des documents.

## app/logging_conf.py
Configure la journalisation de l'application pour enregistrer les événements dans un fichier log et sur la console, facilitant le suivi des activités et l'identification des erreurs.

## app/ingest_docs.py
Module responsable d'ingérer des documents dans Qdrant. Il charge, découpe les textes en chunks, et enregistre ces chunks avec leurs embeddings en utilisant un client Qdrant.

## app/graph.py
Construit et exécute un graphe d'état pour gérer des étapes comme la récupération de la mémoire, la recherche documentaire, le raisonnement, et la réponse aux questions. Utilise LangGraph pour la gestion du graphe d'état.
