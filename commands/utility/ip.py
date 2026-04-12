from commands.base_command import BaseCommand
import asyncio
import discord
from mcstatus import JavaServer
import settings


class Ip(BaseCommand):

    def __init__(self):
        description = "Show server IP details and info"
        params = None
        aliases = ["serverip", "address"]
        super().__init__(description, params, aliases)
        self.category = "Utility"

    async def handle(self, params, message, client):
        server_host = "bryxelrealm.wither.host"
        direct_ip = "23.109.123.215:25614"

        try:
            status = await asyncio.to_thread(self._query_server, server_host)
            status_text = "Online ✅"
            players_text = f"{status.players.online}/{status.players.max}"
            version_text = status.version.name
            latency_text = f"{status.latency:.0f} ms"
            motd_text = status.description or "No MOTD provided"
        except Exception:
            status_text = "Offline or unreachable ❌"
            players_text = "Unknown"
            version_text = "Unknown"
            latency_text = "Unknown"
            motd_text = "No live response available right now."

        embed = discord.Embed(
            title="🌍 BryxelRealm Server Info",
            description="Live server details and connection info.",
            color=discord.Color.teal(),
        )
        embed.add_field(name="Server Host", value=f"`{server_host}`", inline=True)
        embed.add_field(name="Direct IP", value=f"`{direct_ip}`", inline=True)
        embed.add_field(name="Status", value=status_text, inline=False)
        embed.add_field(name="Players", value=players_text, inline=True)
        embed.add_field(name="Minecraft Version", value=version_text, inline=True)
        embed.add_field(name="Latency", value=latency_text, inline=True)
        embed.add_field(name="MOTD", value=motd_text, inline=False)

        embed.set_footer(text="mcstatus checks the Java server status protocol for live info.")

        await message.channel.send(embed=embed)

    def _query_server(self, server_host):
        server = JavaServer.lookup(server_host, timeout=3)
        return server.status()