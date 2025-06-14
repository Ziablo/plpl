# Bot Telegram IA

Un bot Telegram qui utilise l'API OpenAI (GPT-3.5) pour discuter avec les utilisateurs en français.

## Fonctionnalités

- Répond aux messages des utilisateurs en utilisant GPT-3.5
- Réponses en français
- Commandes disponibles :
  - `/start` : Message de bienvenue
  - `/help` : Aide sur l'utilisation du bot

## Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/Ziablo/plpl.git
cd plpl
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Configurer les variables d'environnement :
- Créer un fichier `.env` à la racine du projet
- Ajouter les variables suivantes :
```
TELEGRAM_TOKEN=votre_token_telegram
OPENAI_API_KEY=votre_cle_api_openai
```

## Utilisation

1. Lancer le bot :
```bash
python bot.py
```

2. Sur Telegram :
- Chercher le bot par son nom d'utilisateur
- Envoyer `/start` pour commencer
- Envoyer n'importe quel message pour discuter

## Dépendances

- python-telegram-bot==20.7
- python-dotenv==1.0.0
- openai==1.12.0 