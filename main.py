# userbot.py
import asyncio
import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pytgcalls import PyTgCalls
from pytgcalls.types import StreamType
from pytgcalls.types.input_stream import AudioPiped, InputStream

# ──────────────────────────────────────────────
#  Put your values here (or use environment variables)
API_ID = 20898349          # ← your api id
API_HASH = "9fdb830d1e435b785f536247f49e7d87"
SESSION_STRING = "BQE-4i0Aou5c6ZntfzYmY3MlfS4oKGeocqKjqY1js1gfr5Pnbj-14bZJAjqQ9Zz7i0TYVb7gvqltWE1gzs2KYMheKguZtM_Hm5P6oS80jUypbwbBrMB3ho9hIV7OAC-rniexIGHjDPwlL3HLN-oqW_OU_sK3eJBQDuh5x15uSShz7KaLWA1zwlQQsN-DXHiw0mxuVwYvnNVirvmgBP3fW2STAEPa3FFqnHZ1Hn7OcbCt7YJgzmPVt6TBs5xby_v0ggifLNk_JXYEUE-0bx7GnrqyEztW1DavjVk6eirqIu9IAWdLDUW3FU4V5N0704S8tL3nl2LYDCrtKZ3gfX29sVWWFWiP7AAAAAHKarFXAA"   # ← paste full string session
# ──────────────────────────────────────────────

app = Client(
    name="loud_userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

call_py = PyTgCalls(app)

# Very aggressive loudness chain (still limited by Telegram servers)
LOUD_FILTER = (
    "volume=2.2,"           # gain (careful – too much → clipping / worse quality)
    "acompressor=threshold=-21dB:ratio=12:attack=3:release=80:makeup=15,"
    "alimiter=limit=0.89:attack=2:release=50,"
    "loudnorm=I=-13:TP=-0.8:LRA=6:linear=true"
)

@app.on_message(filters.command("join", prefixes=".") & filters.me)
async def join_voice_chat(client: Client, message: Message):
    if message.chat.id > 0:
        await message.edit_text("Use `.join` **inside a group** with active voice chat.")
        return

    chat_id = message.chat.id

    try:
        # Join (as normal participant)
        await call_py.join_group_call(
            chat_id,
            stream=InputStream(
                AudioPiped(
                    # We use ffmpeg to read microphone (or test file) + apply filters
                    "pipe:0",   # we'll feed raw audio via subprocess
                    bitrate=128000,
                    ffmpeg_filter=LOUD_FILTER
                )
            ),
            stream_type=StreamType().pulse_stream,
        )
        await message.edit_text("✅ Joined voice chat\n(aggressive loudness filters applied)")

    except Exception as e:
        await message.edit_text(f"Error: {str(e)}")


@app.on_message(filters.command("leave", prefixes=".") & filters.me)
async def leave_voice_chat(client: Client, message: Message):
    chat_id = message.chat.id
    try:
        await call_py.leave_group_call(chat_id)
        await message.edit_text("Left voice chat.")
    except Exception as e:
        await message.edit_text(f"Error leaving: {str(e)}")


# ──────────────────────────────────────────────
#  Microphone reader → ffmpeg loud processing → pytgcalls
# ──────────────────────────────────────────────
async def microphone_pipeline():
    """Runs ffmpeg that reads default mic → applies loud filters → outputs raw s16le"""
    cmd = [
        "ffmpeg",
        "-f", "pulse", "-i", "default",               # or alsa, dshow, etc. depending on OS
        "-ac", "1", "-ar", "48000", "-f", "s16le",
        "-af", LOUD_FILTER,
        "pipe:1"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    return process.stdout


# For testing: play loud test tone instead of real mic
async def test_loud_tone():
    cmd = [
        "ffmpeg",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=999999",
        "-af", f"{LOUD_FILTER},volume=2.5",
        "-ac", "1", "-ar", "48000", "-f", "s16le",
        "pipe:1"
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL
    )
    return process.stdout


@app.on_message(filters.command("testloud", prefixes=".") & filters.me)
async def start_test_loud(_, msg: Message):
    if not await call_py.get_call_status(msg.chat.id):
        await msg.edit("First do `.join`")
        return

    await msg.edit("Playing **loud test tone** (sine + aggressive filters)...")

    pipe = await test_loud_tone()

    # You can later change to real mic with: pipe = await microphone_pipeline()

    # pytgcalls can read from pipe directly in newer versions
    # If not → you may need older AudioPiped(path=...) + named pipe trick

    # For simplicity we assume recent pytgcalls supports pipe
    await call_py.change_stream(
        msg.chat.id,
        InputStream(
            AudioPiped(
                pipe,  # file-like object
                bitrate=128000,
                ffmpeg_filter=LOUD_FILTER  # already applied, but kept for safety
            )
        )
    )


async def main():
    await app.start()
    print("Userbot started with string session")
    await call_py.start()
    print("Voice call handler started")
    await asyncio.Event().wait()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())
