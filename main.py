import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message

# Fetching credentials from Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
STRING_SESSION = os.environ.get("STRING_SESSION")
PORT = int(os.environ.get("PORT", 8080))  # Render assigns a PORT dynamically

# Global variables to store original account details
ORIGINAL_NAME = None
ORIGINAL_LAST_NAME = None
ORIGINAL_ABOUT = None

def anti_history_text(text: str) -> str:
    """Replaces normal characters with visually similar Unicode characters 
    and inserts Zero-Width Spaces to completely bypass history tracking bots.
    """
    if not text:
        return ""
    
    # Unicode Homoglyphs Mapping
    char_map = {
        'a': 'а', 'e': 'е', 'i': 'і', 'o': 'о', 'p': 'р',
        'c': 'с', 'y': 'у', 'x': 'х', 'A': 'А', 'B': 'В',
        'E': 'Е', 'K': 'К', 'M': 'М', 'H': 'Н', 'O': 'О',
        'P': 'Р', 'C': 'С', 'T': 'Т', 'X': 'Х', 'Y': 'Ү'
    }
    
    res = "".join(char_map.get(ch, ch) for ch in text)
    return "\u200b".join(list(res))

# Health check server for Render Web Service
async def handle_ping(request):
    return web.Response(text="Userbot is running perfectly on Docker!")

async def main():
    # Initialize Client inside event loop to avoid loop binding errors
    userbot = Client(
        "my_userbot",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=STRING_SESSION
    )

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

            # Obfuscate names using zero-width spaces and homoglyphs
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
        
        try:
            # Uses saved details or defaults to hardcoded values upon restart
            first_name = ORIGINAL_NAME if ORIGINAL_NAME is not None else "˹ɴʏᴍ  ꭙ ᴍᴜꜱɪᴄ˼ ♪"
            last_name = ORIGINAL_LAST_NAME if ORIGINAL_LAST_NAME is not None else ""
            bio = ORIGINAL_ABOUT if ORIGINAL_ABOUT is not None else ""

            # Restore profile text details
            await client.update_profile(
                first_name=first_name,
                last_name=last_name,
                bio=bio
            )
            
            # Delete cloned profile photo (reveals original photo)
            try:
                async for photo in client.get_chat_photos("me"):
                    await client.delete_profile_photos(photo.file_id)
                    break
            except Exception:
                pass
                
            await message.edit("✅ Account successfully restored to original state!")
            
            # Reset state variables
            ORIGINAL_NAME = None
            ORIGINAL_LAST_NAME = None
            ORIGINAL_ABOUT = None

        except Exception as e:
            await message.edit(f"❌ An error occurred: {str(e)}")

    # Start aiohttp web server
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    # Run userbot safely within async context manager
    async with userbot:
        print("Userbot started successfully via Docker Container!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
