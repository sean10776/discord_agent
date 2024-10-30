from enum import Enum

import asyncio
import aiohttp
import discord
from discord import Message
from discord.ext import commands

from utility import config


class AnythingLLM_API:

    def __init__(self, host, api_key, workspace_slug='default'):
        self.loop = asyncio.get_event_loop()

        self.session_id = None
        self.api_ver = '/v1'
        self.host = host

        self.auth_header = {'Authorization': f"Bearer {api_key}"}
        self.api_key = api_key
        self.workspace_slug = workspace_slug

    @property
    def base_api_url(self):
        return self.host + self.api_ver

    async def test_api(self):
        tasks = [self.__test_api__(), self.__test_api_key__(), self.__test_workspace__(self.workspace_slug)]
        print("Testing AnythingLLM API")
        res = await asyncio.gather(*tasks)
        print("API tests completed")

    async def __test_api__(self):
        async with aiohttp.request('GET', self.host) as res:
            assert res.status == 200, "API is not available"
        print("API is available")

    async def __test_api_key__(self):
        async with aiohttp.request('GET', self.base_api_url + '/auth', headers=self.auth_header) as res:
            assert res.status == 200, "API key is not valid"
        print("API key is valid")
            
    async def __test_workspace__(self, workspace):
        async with aiohttp.request('GET', self.base_api_url + f'/workspace/{workspace}', headers=self.auth_header) as res:
            assert res.status == 200, f"Workspace {workspace} does not exist"
            workspaces = await res.json()
            default_slug = ''
            for ws in workspaces['workspace']:
                if ws['slug'] == workspace:
                    print(f"Workspace {workspace}:")
                    return
                if default_slug == '':
                    default_slug = ws['slug']
            print(f"Workspace {workspace} does not exist, using default workspace {default_slug}")
            self.workspace_slug = default_slug
        print("Workspace is valid")

    @property
    async def workspace_info(self):
        async with aiohttp.request('GET', self.base_api_url + f'/workspace/{self.workspace_slug}', 
                                    headers=self.auth_header) as res:
            return res.json()
    
    @property
    def workspace_chats(self):
        async def get_chats():
            async with aiohttp.request('GET', self.base_api_url + f'/workspace/{self.workspace_slug}/chats',
                                    headers=self.auth_header) as res:
                return await res.json()
        return asyncio.run(get_chats())

    async def chat(self, sessionId, message)->aiohttp.ClientResponse:
        async with aiohttp.request('POST', 
                                    self.base_api_url + f'/workspace/{self.workspace_slug}/chat',
                                    headers=self.auth_header, 
                                    json=dict(message = message, mode = 'chat', sessionId = sessionId)
        ) as res:
            if res.status != 200:
                raise Exception(f"Failed to chat: {res.status}")
            return await res.json()

class AI_STATE(Enum):
    OFFLINE = 0
    ONLINE = 1

class AI_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.ai_api = AnythingLLM_API(
            host = config.anythingllm_host,
            api_key = config.anythingllm_api_key,
            workspace_slug = config.anythingllm_workspace_slug
        )
        self.state = AI_STATE.OFFLINE

    async def __test_api__(self):
        try:
            await self.ai_api.test_api()
            self.state = AI_STATE.ONLINE
        except Exception as e:
            print(f"Failed to test API: {e}")
            self.state = AI_STATE.OFFLINE

    async def cog_load(self) -> None:
        print("AI Cog loaded")
        
        try:
            await self.ai_api.test_api()
            self.state = AI_STATE.ONLINE
        except Exception as e:
            print(f"Failed to test API: {e}")
        ...
    
    async def cog_unload(self) -> None:
        ...

    @commands.Cog.listener()
    async def on_message(self, message:Message):
        
        # filter out messages from the bot itself
        if (
            message.author == self.bot.user
            or self.bot.user.id in message.mentions
            or message.channel.type not in (discord.ChannelType.text, discord.ChannelType.public_thread, discord.ChannelType.private_thread)
            or message.author.bot # ignore others bots
            or message.content.startswith(config.discord_prefix) # ignore commands
        ): 
            return
        
        # check if AI is online before processing message
        if self.state == AI_STATE.OFFLINE:
            await message.channel.send("AI is offline. Please try again later.")
            await self.__test_api__()
            return
        
        # print(f"Message: {message.content} from {message.author} in {message.guild}.{message.channel}")
        attachments = message.attachments
        # print(f"Attachments: {attachments}")
        sessionId = f"{message.channel.id}"
        async with message.channel.typing():
            try:
                res = await self.ai_api.chat(sessionId=sessionId, message=message.content)
            except Exception as e:
                print(f"Failed to chat: {e}")
                await message.channel.send("Failed to chat. Please try again later.")
                await self.__test_api__()

            await message.channel.send(res['textResponse'])

async def setup(bot: commands.Bot):
    await bot.add_cog(AI_Cog(bot), guild=discord.Object(id=1291277692389425245))