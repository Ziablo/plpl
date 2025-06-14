import os
import logging
import tempfile
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Changé en DEBUG pour plus de détails
    stream=sys.stdout  # Force l'écriture dans stdout pour Heroku
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

logger.info("Démarrage de l'application...")
logger.info(f"Token trouvé : {'Oui' if TOKEN else 'Non'}")

if not TOKEN:
    logger.error("Token Telegram non trouvé ! Vérifiez votre fichier .env ou les variables d'environnement Heroku.")
    raise ValueError("Token Telegram non trouvé !")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    logger.info(f"Commande /start reçue de {update.effective_user.id}")
    try:
        await update.message.reply_text(
            "👋 Bonjour ! Je suis un bot qui peut télécharger des vidéos.\n"
            "Envoyez-moi un lien de vidéo et je la téléchargerai pour vous."
        )
        logger.info("Message de bienvenue envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la commande start : {str(e)}")
        await update.message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Télécharge et envoie la vidéo"""
    user_id = update.effective_user.id
    url = update.message.text
    logger.info(f"Tentative de téléchargement de {url} par l'utilisateur {user_id}")
    
    # Vérification que c'est bien une URL
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"URL invalide reçue de l'utilisateur {user_id}: {url}")
        await update.message.reply_text("❌ Veuillez envoyer une URL valide.")
        return

    # Message de chargement
    loading_message = await update.message.reply_text("⏳ Téléchargement en cours...")

    try:
        # Création d'un dossier temporaire
        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Dossier temporaire créé : {temp_dir}")
            
            # Configuration de yt-dlp
            ydl_opts = {
                'format': 'best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }

            # Téléchargement de la vidéo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Début du téléchargement pour {url}")
                info = ydl.extract_info(url, download=True)
                video_path = os.path.join(temp_dir, f"{info['title']}.{info['ext']}")
                logger.info(f"Vidéo téléchargée : {video_path}")

            # Envoi de la vidéo
            logger.info(f"Envoi de la vidéo à l'utilisateur {user_id}")
            await update.message.reply_video(
                video=open(video_path, 'rb'),
                caption=f"✅ Voici votre vidéo : {info['title']}"
            )
            logger.info(f"Vidéo envoyée avec succès à l'utilisateur {user_id}")

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement pour l'utilisateur {user_id}: {str(e)}")
        await update.message.reply_text("❌ Une erreur s'est produite lors du téléchargement. Veuillez réessayer avec un autre lien.")
    finally:
        await loading_message.delete()

def main():
    """Fonction principale"""
    logger.info("Démarrage du bot...")
    logger.info(f"Token utilisé : {TOKEN[:10]}...")  # Affiche seulement le début du token pour la sécurité
    
    try:
        # Création de l'application
        application = Application.builder().token(TOKEN).build()
        logger.info("Application créée avec succès")

        # Ajout des handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
        logger.info("Handlers ajoutés avec succès")

        # Démarrage du bot
        logger.info("Démarrage du polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot : {str(e)}")
        raise

if __name__ == '__main__':
    main() 