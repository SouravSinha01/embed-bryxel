import discord
from commands.base_command import BaseCommand


class Donate(BaseCommand):

    def __init__(self):
        description = "Shows the Bryxel Realm webshop and website links"
        params = None
        aliases = ["store", "shop", "website", "site"]
        category = "Utility"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):
        embed = discord.Embed(
            title="Bryxel Realm Store & Website",
            description="Find Bryxel Realm online and support the server via the official webshop.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="Webshop",
            value="[Open the webshop](https://bryxel-realm.tebex.io/)",
            inline=False
        )
        embed.add_field(
            name="Website",
            value="[Open the website](https://bryxelrealm.github.io/BryxelRealm.com/)",
            inline=False
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/889695047510011974/1489989547310977134/store.png?ex=69d26c66&is=69d11ae6&hm=d1bce846054070b2dd10c46ca61acf0d038748b3776febe4c537560c5967114b&")
        embed.set_footer(
            text=f"Requested by {message.author.display_name}",
            icon_url=message.author.avatar.url if message.author.avatar else None
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Webshop",
            style=discord.ButtonStyle.link,
            url="https://bryxel-realm.tebex.io/",
            emoji="🛒"
        ))
        view.add_item(discord.ui.Button(
            label="Website",
            style=discord.ButtonStyle.link,
            url="https://bryxelrealm.github.io/BryxelRealm.com/",
            emoji="🌐"
        ))

        await message.channel.send(embed=embed, view=view)
