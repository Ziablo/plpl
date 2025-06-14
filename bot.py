import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Configuration du logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Chargement des variables d'environnement
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start"""
    await update.message.reply_text(
        "👋 Bonjour ! Je suis un bot qui peut télécharger des vidéos.\n"
        "Envoyez-moi un lien de vidéo et je la téléchargerai pour vous."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Télécharge et envoie la vidéo"""
    url = update.message.text
    
    # Vérification que c'est bien une URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Veuillez envoyer une URL valide.")
        return

    # Message de chargement
    loading_message = await update.message.reply_text("⏳ Téléchargement en cours...")

    try:
        # Configuration de yt-dlp
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
        }

        # Téléchargement de la vidéo
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = f"{info['title']}.{info['ext']}"

        # Envoi de la vidéo
        await update.message.reply_video(
            video=open(video_path, 'rb'),
            caption=f"✅ Voici votre vidéo : {info['title']}"
        )

        # Suppression du fichier temporaire
        os.remove(video_path)
        await loading_message.delete()

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement : {str(e)}")
        await update.message.reply_text("❌ Une erreur s'est produite lors du téléchargement.")
        await loading_message.delete()

def main():
    """Fonction principale"""
    # Création de l'application
    application = Application.builder().token(TOKEN).build()

    # Ajout des handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    # Démarrage du bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 