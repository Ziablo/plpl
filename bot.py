import os
import logging
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import openai

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
logger.info("Chargement des variables d'environnement...")
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuration d'OpenAI
openai.api_key = OPENAI_API_KEY

# Vérification des tokens
if not TELEGRAM_TOKEN:
    logger.error("Token Telegram non trouvé !")
    raise ValueError("Token Telegram non trouvé !")
if not OPENAI_API_KEY:
    logger.error("Clé API OpenAI non trouvée !")
    raise ValueError("Clé API OpenAI non trouvée !")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    await update.message.reply_text(
        "👋 Bonjour ! Je suis un bot IA qui peut discuter avec vous.\n"
        "Envoyez-moi un message et je vous répondrai !"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /help"""
    await update.message.reply_text(
        "🤖 Voici comment m'utiliser :\n\n"
        "• Envoyez-moi n'importe quel message et je vous répondrai\n"
        "• Utilisez /start pour commencer\n"
        "• Utilisez /help pour voir ce message\n\n"
        "Je peux discuter de nombreux sujets et vous aider dans vos questions !"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les messages reçus"""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Message reçu de l'utilisateur {user_id}: {user_message}")
    
    try:
        # Message de chargement
        loading_message = await update.message.reply_text("⏳ Je réfléchis...")
        
        # Appel à l'API OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant IA utile et amical. Répondez en français."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Récupération de la réponse
        ai_response = response.choices[0].message.content
        
        # Suppression du message de chargement
        await loading_message.delete()
        
        # Envoi de la réponse
        await update.message.reply_text(ai_response)
        logger.info(f"Réponse envoyée à l'utilisateur {user_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message : {str(e)}")
        await update.message.reply_text(
            "❌ Désolé, une erreur s'est produite lors du traitement de votre message.\n"
            "Veuillez réessayer plus tard."
        )

def main():
    """Fonction principale"""
    logger.info("=== DÉMARRAGE DU BOT ===")
    
    try:
        # Création de l'application
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Ajout des handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Démarrage du bot
        logger.info("Démarrage du polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot : {str(e)}")
        raise

if __name__ == '__main__':
    main() 