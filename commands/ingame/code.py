from commands.base_command import BaseCommand
import discord
import settings


class Code(BaseCommand):
    def __init__(self):
        description = "Show Minecraft color & formatting codes"
        params = None
        aliases = ["colorcode", "color"]
        category = "Ingame"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):

        embed = discord.Embed(
            title="🎨 Minecraft Color & Format Codes",
            description=f"Use `{settings.COMMAND_PREFIX}&<code>` inside chat.\n──────────────",
            color=discord.Color.from_rgb(88, 101, 242)
        )

        # Attach the image (same directory as bot or correct path)
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1494772848668053504/content.png?ex=69e3d332&is=69e281b2&hm=53f9c7bd5b49bd15a7d99fbcff77bbb020106d99248b28212b0ed3003d6e5b4a&")

        # Optional polish
        if client.user and client.user.avatar:
            embed.set_thumbnail(url=client.user.avatar.url)

        embed.set_footer(
            text=f"Requested by {message.author.display_name}",
            icon_url=message.author.avatar.url if message.author.avatar else None
        )

        await message.channel.send(
           
            embed=embed
        )
