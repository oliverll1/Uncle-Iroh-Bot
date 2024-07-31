from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message
from responses import get_response

# Load environment variables from .env file
load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# Intents
intents = Intents.default()
intents.message_content = True

# Client
client = Client(intents=intents)    


async def send_message(message: Message, user_message: str) -> None:
    if not user_message:
        print("Message was empty")
        return
    
    print(f"User message: {user_message}")
    
    try:
        async with message.channel.typing():
            response: str = get_response(user_message)
            await message.channel.send(response)
       
    except Exception as e:
        print(e)
        print('Something went wrong...')   
        
@client.event
async def on_ready():
    print(f"{client.user} is ready!")

@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    username: str = str(message.author)
    user_message: str = message.content
    channel = message.channel
    
    messages = [ message async for message in channel.history(limit=30) ]
    messages.reverse()
    channel_messages = [ f"\n {message.author}: {message.content}" for message in messages if not message.attachments ]
    channel_messages_text = '\n'.join(channel_messages) + f"\n {username}: {user_message}"

   # print(channel_messages_text)
    await send_message(message, channel_messages_text)

def main() -> None:
    client.run(token=TOKEN)

if __name__ == '__main__':
    main()
