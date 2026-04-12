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
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1490063094607773756/ChatGPT_Image_Apr_5_2026_12_27_58_AM.png?ex=69d2b0e5&is=69d15f65&hm=5d0ee44c980bf7160813cad98d4252c8a86945b798b119c647e9d6bbc7654553&")

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