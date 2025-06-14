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
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
logger.info("Chargement des variables d'environnement...")
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

logger.info("=== DÉMARRAGE DE L'APPLICATION ===")
logger.info(f"Token trouvé : {'Oui' if TOKEN else 'Non'}")
if TOKEN:
    logger.info(f"Token (premiers caractères) : {TOKEN[:10]}...")

if not TOKEN:
    logger.error("Token Telegram non trouvé ! Vérifiez votre fichier .env ou les variables d'environnement Heroku.")
    raise ValueError("Token Telegram non trouvé !")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    logger.info("=== COMMANDE START RECUE ===")
    logger.info(f"Utilisateur : {update.effective_user.id}")
    logger.info(f"Message : {update.message.text}")
    
    try:
        logger.info("Envoi du message de bienvenue...")
        await update.message.reply_text(
            "👋 Bonjour ! Je suis un bot qui peut télécharger des vidéos.\n"
            "Envoyez-moi un lien de vidéo et je la téléchargerai pour vous."
        )
        logger.info("Message de bienvenue envoyé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de la commande start : {str(e)}")
        logger.exception("Détails de l'erreur :")
        await update.message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Télécharge et envoie la vidéo"""
    user_id = update.effective_user.id
    url = update.message.text
    logger.info(f"=== TENTATIVE DE TÉLÉCHARGEMENT ===")
    logger.info(f"Utilisateur : {user_id}")
    logger.info(f"URL : {url}")
    
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
                'format': 'best[filesize<50M]',  # Limite la taille à 50MB
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'postprocessor_args': [
                    '-c:v', 'libx264',
                    '-crf', '28',  # Compression plus agressive
                    '-preset', 'ultrafast',
                    '-c:a', 'aac',
                    '-b:a', '128k'
                ],
            }

            # Téléchargement de la vidéo
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info(f"Début du téléchargement pour {url}")
                info = ydl.extract_info(url, download=True)
                video_path = os.path.join(temp_dir, f"{info['title']}.{info['ext']}")
                logger.info(f"Vidéo téléchargée : {video_path}")

            # Envoi de la vidéo
            logger.info(f"Envoi de la vidéo à l'utilisateur {user_id}")
            
            # Vérification de la taille du fichier
            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:  # 50MB en bytes
                await update.message.reply_text("❌ La vidéo est trop grande (plus de 50MB). Veuillez essayer avec une vidéo plus courte.")
                return
                
            await update.message.reply_video(
                video=open(video_path, 'rb'),
                caption=f"✅ Voici votre vidéo : {info['title']}"
            )
            logger.info(f"Vidéo envoyée avec succès à l'utilisateur {user_id}")

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement pour l'utilisateur {user_id}: {str(e)}")
        logger.exception("Détails de l'erreur :")
        await update.message.reply_text("❌ Une erreur s'est produite lors du téléchargement. Veuillez réessayer avec un autre lien.")
    finally:
        await loading_message.delete()

def main():
    """Fonction principale"""
    logger.info("=== DÉMARRAGE DU BOT ===")
    
    try:
        # Création de l'application
        logger.info("Création de l'application...")
        application = Application.builder().token(TOKEN).build()
        logger.info("Application créée avec succès")

        # Ajout des handlers
        logger.info("Ajout des handlers...")
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
        logger.info("Handlers ajoutés avec succès")

        # Démarrage du bot
        logger.info("Démarrage du polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du bot : {str(e)}")
        logger.exception("Détails de l'erreur :")
        raise

if __name__ == '__main__':
    main() 