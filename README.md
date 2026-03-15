# Discord Feature Bot

A personal Discord bot that i run locally. Built with Python and discord.py.

## Features
- Auto-replies to specific users with random text, GIFs, or images
- Send DMs to users via commands
- Tag system for saving and retrieving custom responses
- Owner-only — only I can use it
- can use it for trolling xD

## Commands
| Command | Description |
|---|---|
| `-hi` | Say hi to the bot |
| `-tag <key>` | Look up a saved tag |
| `-tags` | List all available tags |
| `-info` | Show bot stats |
| `-dm @user <message>` | Send a DM to a user |
| `-dmgif @user <url>` | Send a GIF DM to a user |

## Running Locally
1. Clone the repo
2. Install dependencies: `pip3 install discord.py python-dotenv flask`
3. Create a `.env` file with your bot token and owner ID:
    ```
    BOT_TOKEN=your_token_here
    OWNER_ID=your_discord_id_here
    ```
4. Run the bot: `python3 dcb.py`

It is being run locally on my machine and i dont plan it to host 24/7 anytime soon :)
