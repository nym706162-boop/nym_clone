import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Fetching credentials from Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")

userbot = Client(
    "my_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

# Global variables to store original account details
ORIGINAL_NAME = None
ORIGINAL_LAST_NAME = None
ORIGINAL_ABOUT = None

def anti_history_text(text: str) -> str:
    """Inserts a Zero-Width Space (\u200b) between characters 

    to bypass history tracking bots.
    """
    if not text:
        return ""
    return "\u200b".join(list(text))

@userbot.on_message(filters.command("clone", prefixes=["/", "."]) & filters.me)
async def clone(client: Client, message: Message):
    global ORIGINAL_NAME, ORIGINAL_LAST_NAME, ORIGINAL_ABOUT
    
    if len(message.command) < 2:
        await message.edit("Please provide a username to clone! (e.g., .clone @username)")
        return

    try:
        target = message.command[1].replace("@", "")
        target_chat = await client.get_chat(target)
        
        # Save original account info before performing the clone
        if not ORIGINAL_NAME:
            me = await client.get_chat("me")
            ORIGINAL_NAME = me.first_name or ""
            ORIGINAL_LAST_NAME = me.last_name or ""
            ORIGINAL_ABOUT = me.bio or ""

        # Dummy profile update to interrupt rapid history-bot logs
        await client.update_profile(first_name="Telegram User", last_name="")
        await asyncio.sleep(1)

        raw_first_name = target_chat.first_name or target_chat.title or ""
        raw_last_name = target_chat.last_name or ""
        raw_bio = target_chat.bio or ""

        # Obfuscate names using zero-width spaces
        first_name = anti_history_text(raw_first_name)
        last_name = anti_history_text(raw_last_name)
        bio = raw_bio[:70]  # Telegram bio limit is 70 characters
        
        # Apply cloned profile details
        await client.update_profile(
            first_name=first_name,
            last_name=last_name,
            bio=bio
        )
        
        # Download and set profile photo if available
        if target_chat.photo:
            photo_path = await client.download_media(target_chat.photo.big_file_id)
            await client.set_profile_photo(photo=photo_path)
            if os.path.exists(photo_path):
                os.remove(photo_path)  # Cleanup local storage

        await message.edit("✅ Account successfully cloned (Anti-History Enabled)!")
    
    except Exception as e:
        await message.edit(f"❌ An error occurred: {str(e)}")

@userbot.on_message(filters.command("unclone", prefixes=["/", "."]) & filters.me)
async def unclone(client: Client, message: Message):
    global ORIGINAL_NAME, ORIGINAL_LAST_NAME, ORIGINAL_ABOUT
    
    if ORIGINAL_NAME is None:
        await message.edit("⚠️ No saved profile state found to restore!")
        return

    try:
        # Restore original profile details
        await client.update_profile(
            first_name=ORIGINAL_NAME,
            last_name=ORIGINAL_LAST_NAME,
            bio=ORIGINAL_ABOUT
        )
        
        # Remove the latest added profile photo
        async for photo in client.get_chat_photos("me"):
            await client.delete_profile_photos(photo.file_id)
            break
            
        await message.edit("✅ Account successfully restored to original state!")
        
        # Reset state variables
        ORIGINAL_NAME = None
        ORIGINAL_LAST_NAME = None
        ORIGINAL_ABOUT = None

    except Exception as e:
        await message.edit(f"❌ An error occurred: {str(e)}")

userbot.run()
