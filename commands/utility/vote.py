from commands.base_command import BaseCommand
import discord
import settings


class Vote(BaseCommand):

    def __init__(self):
        description = "Get voting links to support the server!"
        params = None
        aliases = ["voting", "votes","v","vote"]
        category = "Utility"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):
        embed = discord.Embed(
            title="🗳️ Vote for BryxelRealm!",
            description="Help support our Minecraft server by voting on these sites! Each vote helps us grow and provides rewards for players.\n\nClick the buttons below to vote:",
            color=discord.Color.green()
        )

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/889695047510011974/1488887642626981938/image.png?ex=69ce6a2c&is=69cd18ac&hm=2246c72f9ab347e3bd60f7551e9e632a9555a5d74b40c2b29c725c6af942d08e&")  # Optional: add a Minecraft logo
        embed.set_footer(text="Thank you for your support! 🎮", icon_url=message.guild.icon.url if message.guild.icon else None)

        # Create buttons for each voting site
        view = discord.ui.View()

        # MCLIST
        view.add_item(discord.ui.Button(
            label="MCLIST",
            style=discord.ButtonStyle.link,
            url="https://mclist.io/server/75660-bryxelrealm-wither-host-bryxel-realmnow-on-1/vote",
            emoji="🗳️"
        ))

        # MINECRAFT SERVERS-NET
        view.add_item(discord.ui.Button(
            label="MINECRAFT SERVERS-NET",
            style=discord.ButtonStyle.link,
            url="https://minecraft-server.net/vote/BryxelRealm/",
            emoji="🌐"
        ))

        # MINECRAFT MP
        view.add_item(discord.ui.Button(
            label="MINECRAFT MP",
            style=discord.ButtonStyle.link,
            url="https://minecraft-mp.com/server/347865/vote/",
            emoji="🎯"
        ))

        # TOPMINECRAFTSERVERS
        view.add_item(discord.ui.Button(
            label="TOPMINECRAFTSERVERS",
            style=discord.ButtonStyle.link,
            url="https://topminecraftservers.org/server/41157",
            emoji="⭐"
        ))

        # MINECRAFT.BUZZ
        view.add_item(discord.ui.Button(
            label="MINECRAFT.BUZZ",
            style=discord.ButtonStyle.link,
            url="https://minecraft.buzz/vote/17488",
            emoji="🐝"
        ))

        await message.channel.send(embed=embed, view=view)
