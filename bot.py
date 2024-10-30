import logging.handlers
from typing import List, Optional

import asyncio
import discord
from discord.ext import commands
import logging

from utility import config

ver = '0.0.1'
INVITE_MSG= "======================" + \
            "\nBOT INVITE URL: \n" + \
            "https://discord.com/oauth2/authorize?client_id={id}&permissions=412317273088&scope=bot\n" + \
            "======================"

class MyBot(commands.Bot):
    def __init__(
            self, 
            *args,
            extensions: List[str] = None,
            testing_guild_id: Optional[int] = None,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.testing_guild_id = testing_guild_id
        self.initial_extensions = extensions or []
    
    async def on_ready(self):
        print(f"Version: {ver}")
        print(f"Logged in as {self.user}")
        print(INVITE_MSG.format(id=self.user.id))

    async def setup_hook(self) -> None:
        print("Setting up bot")

        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                cog = self.get_cog(extension)
                if cog:
                    print(f"Loaded extension {extension}")
                    for cmd in cog.get_commands():
                        print(f"=>{cmd.name}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")

        if self.testing_guild_id:
            guild = discord.Object(self.testing_guild_id)
            
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

async def main():
    # setup logging
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        mode='w',
        maxBytes=32*1024*1024,
        backupCount=5
    )
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    
    # setup bot
    exts = ['cogs.ai_cog']
    intents = discord.Intents.default()
    intents.message_content = True

    async with MyBot(
        command_prefix=config.discord_prefix,
        testing_guild_id=config.discord_test_guild_id, 
        intents=intents, 
        extensions=exts
    ) as bot:
        @bot.command()
        async def load(ctx, extension):
            print(f"Loading extension {extension}")
            await bot.load_extension(f"cogs.{extension}")
            await ctx.send(f"Loaded extension {extension}")

        @bot.command()
        async def unload(ctx, extension):
            await bot.unload_extension(f"cogs.{extension}")
            await ctx.send(f"Unloaded extension {extension}")

        @bot.command()
        async def reload(ctx, extension):
            await bot.reload_extension(f"cogs.{extension}")
            await ctx.send(f"Reloaded extension {extension}")

        @bot.command()
        async def cogs(ctx):
            await ctx.send(f"Extensions: {bot.extensions.keys()}")

        await bot.start(config.discord_token)

if __name__ == '__main__':
    asyncio.run(main())