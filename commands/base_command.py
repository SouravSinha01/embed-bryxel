import asyncio

import discord

import settings
from rate_limiter import get_global_limiter

# Base command class
# Do not modify!
class BaseCommand:
    def __init__(self, description, params, aliases=None, category="Other"):
        self.name = type(self).__name__.lower()
        self.params = params
        self.aliases = aliases or []
        self.category = category
        self.summary = description

        desc = f"**{settings.COMMAND_PREFIX}{self.name}**"
        if self.aliases:
            desc += f" (aliases: {', '.join(settings.COMMAND_PREFIX + a for a in self.aliases)})"
        if self.params:
            desc += " " + " ".join(f"*<{p}>*" for p in params)
        desc += f": {description}."
        self.description = desc

    async def _safe_send(self, channel, **kwargs):
        try:
            await get_global_limiter().acquire()
            return await channel.send(**kwargs)
        except discord.errors.HTTPException as exc:
            if exc.status == 429:
                retry_after = getattr(exc, "retry_after", None)
                if retry_after:
                    await asyncio.sleep(float(retry_after))
                    try:
                        await get_global_limiter().acquire()
                        return await channel.send(**kwargs)
                    except discord.errors.HTTPException as retry_exc:
                        if retry_exc.status == 429:
                            return None
                        raise
                return None
            raise
