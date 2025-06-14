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

    # Vérification des domaines supportés
    supported_domains = [
        'youtube.com', 'youtu.be',
        'vimeo.com',
        'dailymotion.com',
        'facebook.com', 'fb.watch',
        'instagram.com',
        'tiktok.com'
    ]
    
    if not any(domain in url.lower() for domain in supported_domains):
        logger.warning(f"Domaine non supporté reçu de l'utilisateur {user_id}: {url}")
        await update.message.reply_text(
            "❌ Ce site n'est pas supporté. Les sites supportés sont :\n"
            "• YouTube\n"
            "• Vimeo\n"
            "• Dailymotion\n"
            "• Facebook\n"
            "• Instagram\n"
            "• TikTok"
        )
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
                'verbose': True,  # Ajout de logs détaillés
                'extract_flat': False,
                'ignoreerrors': False,
                # Configuration des cookies
                'cookiefile': 'cookies.txt',  # Fichier de cookies
                'cookiesfrombrowser': None,  # Désactive la récupération des cookies du navigateur
            }

            # Vérification de l'existence du fichier de cookies
            if not os.path.exists('cookies.txt'):
                logger.warning("Fichier de cookies non trouvé")
                await update.message.reply_text(
                    "⚠️ Cette vidéo nécessite une connexion.\n"
                    "Pour télécharger des vidéos privées, vous devez d'abord :\n"
                    "1. Vous connecter au site dans votre navigateur\n"
                    "2. Exporter les cookies avec l'extension 'Get cookies.txt'\n"
                    "3. Envoyer le fichier cookies.txt au bot"
                )
                return

            # Téléchargement de la vidéo
            try:
                logger.info(f"Début du téléchargement pour {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    logger.info("Extraction des informations de la vidéo...")
                    info = ydl.extract_info(url, download=True)
                    if not info:
                        raise Exception("Impossible d'extraire les informations de la vidéo")
                    
                    logger.info(f"Informations extraites : {info.get('title', 'Titre inconnu')}")
                    video_path = os.path.join(temp_dir, f"{info['title']}.{info['ext']}")
                    logger.info(f"Chemin de la vidéo : {video_path}")
                    
                    if not os.path.exists(video_path):
                        raise Exception(f"Le fichier n'a pas été créé : {video_path}")
                    
                    logger.info(f"Taille du fichier : {os.path.getsize(video_path)} bytes")
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction/téléchargement : {str(e)}")
                raise

            # Vérification de la taille du fichier
            file_size = os.path.getsize(video_path)
            logger.info(f"Taille finale du fichier : {file_size} bytes")
            if file_size > 50 * 1024 * 1024:  # 50MB en bytes
                await update.message.reply_text("❌ La vidéo est trop grande (plus de 50MB). Veuillez essayer avec une vidéo plus courte.")
                return

            # Envoi de la vidéo
            try:
                logger.info(f"Préparation de l'envoi de la vidéo à l'utilisateur {user_id}")
                with open(video_path, 'rb') as video_file:
                    logger.info("Fichier ouvert avec succès")
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"✅ Voici votre vidéo : {info['title']}"
                    )
                logger.info(f"Vidéo envoyée avec succès à l'utilisateur {user_id}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de la vidéo : {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement pour l'utilisateur {user_id}: {str(e)}")
        logger.exception("Détails de l'erreur :")
        
        # Message d'erreur plus détaillé
        error_message = "❌ Une erreur s'est produite lors du téléchargement.\n"
        if "Video unavailable" in str(e):
            error_message += "La vidéo n'est pas disponible ou est privée."
        elif "Sign in" in str(e):
            error_message += "Cette vidéo nécessite une connexion."
        elif "filesize" in str(e):
            error_message += "La vidéo est trop grande (plus de 50MB)."
        elif "Unable to download webpage" in str(e):
            error_message += "Impossible d'accéder à la vidéo. Vérifiez que l'URL est correcte."
        elif "This video is unavailable" in str(e):
            error_message += "Cette vidéo n'est pas disponible dans votre pays ou a été supprimée."
        else:
            error_message += f"Erreur technique : {str(e)}"
            
        await update.message.reply_text(error_message)
    finally:
        await loading_message.delete()

async def handle_cookies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère l'envoi du fichier de cookies"""
    if not update.message.document:
        await update.message.reply_text("❌ Veuillez envoyer un fichier cookies.txt")
        return

    if update.message.document.file_name != "cookies.txt":
        await update.message.reply_text("❌ Le fichier doit s'appeler 'cookies.txt'")
        return

    try:
        # Téléchargement du fichier
        file = await context.bot.get_file(update.message.document.file_id)
        await file.download_to_drive("cookies.txt")
        await update.message.reply_text("✅ Fichier de cookies reçu avec succès ! Vous pouvez maintenant télécharger des vidéos privées.")
    except Exception as e:
        logger.error(f"Erreur lors de la réception du fichier de cookies : {str(e)}")
        await update.message.reply_text("❌ Une erreur s'est produite lors de la réception du fichier de cookies.")

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
        application.add_handler(MessageHandler(filters.Document.ALL, handle_cookies))
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