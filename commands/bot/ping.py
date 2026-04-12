from commands.base_command import BaseCommand
import discord
import settings
import json
import os
import platform
import socket
import struct
import time

try:
    import psutil
except ImportError:
    psutil = None


class Ping(BaseCommand):

    def __init__(self):
        description = (
            "Show bot latency, runtime stats, library info, and optional Minecraft server status"
        )
        params = None
        aliases = ["pong", "latency"]
        category = "Bot"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):
        start = time.perf_counter()
        placeholder = await message.channel.send("🏓 Pinging...")
        elapsed_ms = (time.perf_counter() - start) * 1000

        discord_version = getattr(discord, "__version__", "unknown")
        python_version = platform.python_version()
        cpu_count = os.cpu_count() or "unknown"
        cpu_name = platform.processor() or "unknown"

        if psutil:
            process = psutil.Process(os.getpid())
            cpu_percent = process.cpu_percent(interval=None)
            memory_mb = process.memory_info().rss / 1024 ** 2
            uptime = time.time() - process.create_time()
            uptime_text = self._format_seconds(int(uptime))
            cpu_usage = f"{cpu_percent:.1f}%"
            memory_text = f"{memory_mb:.1f} MB"
        else:
            cpu_usage = "psutil not installed"
            memory_text = "psutil not installed"
            uptime_text = "psutil not installed"

        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.blue(),
            description="Bot ping and system information."
        )
        embed.add_field(name="Discord Gateway Latency", value=f"{client.latency * 1000:.0f} ms", inline=False)
        embed.add_field(name="Message Response Time", value=f"{elapsed_ms:.0f} ms", inline=False)
        embed.add_field(name="Discord.py", value=f"{discord_version}", inline=True)
        embed.add_field(name="Python", value=python_version, inline=True)
        embed.add_field(name="CPU", value=f"{cpu_name}\nCores: {cpu_count}", inline=False)
        embed.add_field(name="CPU Usage", value=cpu_usage, inline=True)
        embed.add_field(name="Memory", value=memory_text, inline=True)
        embed.add_field(name="Process Uptime", value=uptime_text, inline=False)
        embed.set_footer(text="Optional: use `.ping <host> [port]` to check a Minecraft server.")

        if params:
            host_port = self._parse_host_port(params)
            if host_port[0] is None:
                embed.add_field(name="Minecraft Server", value="Invalid host or port", inline=False)
            else:
                host, port = host_port
                mc_status = self._query_minecraft_server(host, port)
                embed.add_field(name="Minecraft Server", value=mc_status["status"], inline=False)
                if mc_status.get("details"):
                    for line in mc_status["details"]:
                        embed.add_field(name=line[0], value=line[1], inline=False)

        await placeholder.edit(content=None, embed=embed)

    def _parse_host_port(self, params):
        host = params[0]
        port = 25565

        if ":" in host:
            try:
                host, port_str = host.rsplit(":", 1)
                port = int(port_str)
            except ValueError:
                return None, None

        if len(params) > 1:
            try:
                port = int(params[1])
            except ValueError:
                return None, None

        return host, port

    def _query_minecraft_server(self, host, port):
        try:
            with socket.create_connection((host, port), timeout=4) as sock:
                sock.settimeout(4)
                self._send_handshake(sock, host, port)
                self._send_request(sock)

                packet = self._receive_packet(sock)
                packet_id, index = self._read_varint(packet, 0)
                if packet_id != 0:
                    return {"status": "Unexpected response from server", "details": []}

                json_length, size_length = self._read_varint(packet, index)
                json_start = index + size_length
                json_data = packet[json_start : json_start + json_length].decode("utf-8")
                data = json.loads(json_data)

                description = self._parse_description(data.get("description", "Unknown"))
                players = data.get("players", {})
                version = data.get("version", {}).get("name", "Unknown")
                online = players.get("online", "?")
                max_players = players.get("max", "?")

                details = [
                    ("Status", "Online"),
                    ("Version", version),
                    ("Players", f"{online}/{max_players}"),
                    ("Description", description),
                ]
                return {"status": f"Online ({host}:{port})", "details": details}
        except (socket.timeout, ConnectionRefusedError, OSError, ValueError):
            return {"status": f"Offline or unreachable ({host}:{port})", "details": []}

    def _send_handshake(self, sock, host, port):
        data = bytearray()
        data.extend(self._pack_varint(754))
        data.extend(self._pack_string(host))
        data.extend(struct.pack(">H", port))
        data.extend(self._pack_varint(1))
        self._send_packet(sock, 0x00, bytes(data))

    def _send_request(self, sock):
        self._send_packet(sock, 0x00, b"")

    def _send_packet(self, sock, packet_id, payload):
        packet = self._pack_varint(packet_id) + payload
        sock.sendall(self._pack_varint(len(packet)) + packet)

    def _receive_packet(self, sock):
        length = self._read_varint_from_socket(sock)
        return self._receive_exact(sock, length)

    def _receive_exact(self, sock, count):
        data = bytearray()
        while len(data) < count:
            chunk = sock.recv(count - len(data))
            if not chunk:
                raise OSError("Connection closed")
            data.extend(chunk)
        return bytes(data)

    def _read_varint_from_socket(self, sock):
        num_read = 0
        result = 0
        while True:
            byte = sock.recv(1)
            if not byte:
                raise OSError("Connection closed")
            value = byte[0]
            result |= (value & 0x7F) << (7 * num_read)
            num_read += 1
            if num_read > 5:
                raise ValueError("VarInt too big")
            if not (value & 0x80):
                break
        return result

    def _read_varint(self, data, index):
        num_read = 0
        result = 0
        while True:
            if index + num_read >= len(data):
                raise ValueError("Incomplete VarInt")
            value = data[index + num_read]
            result |= (value & 0x7F) << (7 * num_read)
            num_read += 1
            if num_read > 5:
                raise ValueError("VarInt too big")
            if not (value & 0x80):
                break
        return result, num_read

    def _pack_varint(self, value):
        result = bytearray()
        while True:
            temp = value & 0x7F
            value >>= 7
            if value != 0:
                temp |= 0x80
            result.append(temp)
            if value == 0:
                break
        return bytes(result)

    def _pack_string(self, value):
        encoded = value.encode("utf-8")
        return self._pack_varint(len(encoded)) + encoded

    def _parse_description(self, description):
        if isinstance(description, dict):
            return description.get("text", str(description))
        return str(description)

    def _format_seconds(self, seconds):
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {sec}s"
        if minutes:
            return f"{minutes}m {sec}s"
        return f"{sec}s"
