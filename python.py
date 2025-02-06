import os
from urllib.parse import urlparse, parse_qs
import re
import requests  # For handling URL redirection
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)
import logging

AFFILIATE_TAG = 'subh0705-21'
TOKEN = '7750214199:AAFdf8U6mr2T5awgFpeXRy_y31CerftwYoI'  # Replace with your actual bot token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_link(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])

def extract_asin(url):
    # Resolve the URL in case it's a shortened URL
    try:
        response = requests.get(url, allow_redirects=True)
        resolved_url = response.url
    except requests.RequestException:
        # If there's an error resolving the URL, use the original
        resolved_url = url

    # Regular expression to find ASIN in URL
    asin_pattern = re.compile(r'/([A-Z0-9]{10})(?:[/?]|$)', re.IGNORECASE)
    match = asin_pattern.search(resolved_url)
    if match:
        return match.group(1).upper()
    
    parsed_url = urlparse(resolved_url)
    query_params = parse_qs(parsed_url.query)
    
    # Check query parameters for ASIN
    for param in query_params:
        if param.lower() == 'asin' and len(query_params[param][0]) == 10:
            return query_params[param][0].upper()
    
    return None

def normalize_link(asin):
    base_url = 'https://www.amazon.in/dp/'
    normalized_url = f"{base_url}{asin}?tag={AFFILIATE_TAG}"
    return normalized_url

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Send me the Amazon product URL, and I will generate the affiliate link!'
    )

async def generate_affiliate_link(update: Update, context: CallbackContext) -> None:
    product_url = update.message.text.strip()
    if not is_valid_link(product_url):
        await update.message.reply_text('Please provide a valid Amazon product URL.')
        return
    
    asin = extract_asin(product_url)
    if asin:
        affiliate_link = normalize_link(asin)
        await update.message.reply_text(f"Here's your affiliate link: {affiliate_link}")
    else:
        await update.message.reply_text(
            'Unable to extract ASIN from the provided URL. Please provide a valid Amazon product URL.'
        )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, generate_affiliate_link)
    )

    # For deployment on Render, set up the webhook
    PORT = int(os.environ.get('PORT', '8443'))
    HOST = '0.0.0.0'  # Binding to all interfaces
    HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

    if HOSTNAME:
        # Set up webhook URL
        webhook_url = f"https://{HOSTNAME}/{TOKEN}"
        logger.info(f"Setting webhook to {webhook_url}")

        application.run_webhook(
            listen=HOST,
            port=PORT,
            url_path=TOKEN,
            webhook_url=webhook_url,
        )
    else:
        # If HOSTNAME is not set, fall back to polling (useful for local testing)
        logger.info("RENDER_EXTERNAL_HOSTNAME not set, using long polling")
        application.run_polling()

if __name__ == '__main__':
    main()
