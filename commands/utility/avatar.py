import discord
import settings
from commands.base_command import BaseCommand


class Avatar(BaseCommand):

    def __init__(self):
        description = "Shows a user's avatar URL and image"
        params = ["user"]
        aliases = ["av"]
        category = "Utility"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):
        target = None

        if message.mentions:
            target = message.mentions[0]
        elif params:
            user_id = params[0].strip()
            if user_id.isdigit():
                try:
                    snowflake = int(user_id)
                    if message.guild:
                        target = message.guild.get_member(snowflake)
                    if target is None:
                        target = await client.fetch_user(snowflake)
                except (ValueError, discord.NotFound):
                    target = None

        if target is None:
            target = message.author if not params else None

        if target is None:
            await self._safe_send(
                message.channel,
                content=f"Usage: `{settings.COMMAND_PREFIX}avatar @user` or `{settings.COMMAND_PREFIX}avatar <user_id>`"
            )
            return

        avatar_url = target.avatar.url if getattr(target, "avatar", None) else target.default_avatar.url

        embed = discord.Embed(
            title=f"{target.display_name}'s Avatar",
            description=f"Here is the avatar for {target.mention}",
            color=discord.Color.blue()
        )
        embed.set_image(url=avatar_url)
        embed.add_field(
            name="Avatar URL",
            value=f"[Open avatar]({avatar_url})",
            inline=False
        )
        embed.set_footer(
            text=f"Requested by {message.author.display_name}",
            icon_url=message.author.avatar.url if message.author.avatar else None
        )

        await self._safe_send(message.channel, embed=embed)
