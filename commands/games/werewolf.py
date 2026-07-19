import asyncio
import random

import discord

import settings
from commands.base_command import BaseCommand


VOTE_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")
LOBBIES = {}


class Werewolf(BaseCommand):
	def __init__(self):
		description = "Host and play Werewolf using a lobby-based day and night cycle"
		params = None
		aliases = ["ww", "wolf"]
		category = "Games"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		if not message.guild:
			await self._safe_send(message.channel, content="Werewolf can only be played in a server.")
			return

		if not params:
			await self._send_help(message)
			return

		action = params[0].lower()
		lobby_id = params[1].lower() if len(params) > 1 else None
		if action not in {"create", "join", "start", "inspect", "status", "end"}:
			await self._send_help(message)
			return
		if not lobby_id:
			await self._safe_send(
				message.channel,
				content=f"Missing lobby ID. Try `{settings.COMMAND_PREFIX}ww {action} mygame`.",
			)
			return

		if action == "create":
			await self._create(lobby_id, message)
		elif action == "join":
			await self._join(lobby_id, message)
		elif action == "start":
			await self._start(lobby_id, message, client)
		elif action == "inspect":
			await self._inspect(lobby_id, message)
		elif action == "status":
			await self._status(lobby_id, message)
		else:
			await self._end(lobby_id, message)

	async def _send_help(self, message):
		prefix = settings.COMMAND_PREFIX
		embed = discord.Embed(
			title="🐺 Werewolf",
			description="Create a lobby, gather 4–10 players, then survive the day/night cycle.",
			color=discord.Color.dark_red(),
		)
		embed.add_field(
			name="Lobby commands",
			value=(
				f"`{prefix}ww create <lobby>`\n"
				f"`{prefix}ww join <lobby>`\n"
				f"`{prefix}ww start <lobby>`\n"
				f"`{prefix}ww status <lobby>`\n"
				f"`{prefix}ww end <lobby>`"
			),
			inline=False,
		)
		embed.add_field(
			name="Aura Seer",
			value=f"During the day: `{prefix}ww inspect <lobby> @player`",
			inline=False,
		)
		embed.set_footer(text="The lobby creator controls start and end.")
		await self._safe_send(message.channel, embed=embed)

	async def _create(self, lobby_id, message):
		key = (message.guild.id, lobby_id)
		if key in LOBBIES:
			await self._safe_send(message.channel, content=f"A lobby named `{lobby_id}` already exists.")
			return
		LOBBIES[key] = {
			"id": lobby_id,
			"guild": message.guild,
			"game_channel": message.channel,
			"owner_id": message.author.id,
			"players": {message.author.id: message.author},
			"roles": {},
			"alive": set(),
			"phase": "setup",
			"started": False,
			"wolf_channel": None,
			"used_inspect": set(),
			"task": None,
		}
		await self._safe_send(
			message.channel,
			content=(f"🎮 Lobby `{lobby_id}` created by {message.author.mention}. You joined automatically.\n"
					 f"Join with `{settings.COMMAND_PREFIX}ww join {lobby_id}`."),
		)

	async def _join(self, lobby_id, message):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		if lobby["started"]:
			await self._safe_send(message.channel, content="That game has already started.")
			return
		if message.author.bot:
			return
		if message.author.id in lobby["players"]:
			await self._safe_send(message.channel, content="You are already in that lobby.")
			return
		if len(lobby["players"]) >= len(VOTE_EMOJIS):
			await self._safe_send(message.channel, content="This lobby is full (10 players maximum).")
			return
		lobby["players"][message.author.id] = message.author
		await self._safe_send(message.channel, content=f"✅ {message.author.mention} joined `{lobby_id}`.")

	async def _start(self, lobby_id, message, client):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		if message.author.id != lobby["owner_id"]:
			await self._safe_send(message.channel, content="Only the lobby creator can start the game.")
			return
		if lobby["started"]:
			await self._safe_send(message.channel, content="That game has already started.")
			return
		if len(lobby["players"]) < 4:
			await self._safe_send(message.channel, content="At least 4 players are required.")
			return

		players = list(lobby["players"].values())
		role_names = self._build_roles(len(players))
		random.shuffle(role_names)
		lobby["roles"] = {player.id: role for player, role in zip(players, role_names)}
		lobby["alive"] = set(lobby["players"])
		lobby["started"] = True
		lobby["phase"] = "starting"

		try:
			for player in players:
				await player.send(f"🐺 Your role in lobby `{lobby_id}` is **{lobby['roles'][player.id]}**.")
		except discord.HTTPException:
			lobby["started"] = False
			lobby["phase"] = "setup"
			await self._safe_send(
				message.channel,
				content="I could not DM every player. Everyone must enable server-member DMs before starting.",
			)
			return

		try:
			await self._create_wolf_channel(lobby, client)
		except (discord.Forbidden, discord.HTTPException):
			lobby["started"] = False
			lobby["phase"] = "setup"
			await self._safe_send(message.channel, content="I need Manage Channels permission to start Werewolf.")
			return

		counts = {name: role_names.count(name) for name in set(role_names)}
		await self._safe_send(
			message.channel,
			content=(f"🌙 Werewolf started in `{lobby_id}` with {len(players)} players. "
					 f"Roles: {', '.join(f'{count} {name}' for name, count in sorted(counts.items()))}."),
		)
		lobby["task"] = asyncio.create_task(self._game_loop(lobby, client))

	def _build_roles(self, player_count):
		wolves = 2 if player_count >= 8 else 1
		doctors = 1 if player_count >= 8 else 0
		seers = 1
		return (["Werewolf"] * wolves + ["Aura Seer"] * seers + ["Doctor"] * doctors
				+ ["Villager"] * (player_count - wolves - seers - doctors))

	async def _create_wolf_channel(self, lobby, client):
		guild = lobby["guild"]
		bot_member = guild.me or guild.get_member(client.user.id)
		overwrites = {
			guild.default_role: discord.PermissionOverwrite(view_channel=False),
			bot_member: discord.PermissionOverwrite(view_channel=True, send_messages=True),
		}
		for player_id, role in lobby["roles"].items():
			if role == "Werewolf":
				overwrites[lobby["players"][player_id]] = discord.PermissionOverwrite(
					view_channel=True, send_messages=True
				)
		lobby["wolf_channel"] = await guild.create_text_channel(
			f"werewolf-{lobby['id']}", overwrites=overwrites, reason="Werewolf game channel"
		)

	async def _game_loop(self, lobby, client):
		try:
			while self._winner(lobby) is None:
				lobby["phase"] = "night"
				await lobby["game_channel"].send("🌙 Night falls. Werewolves have 60 seconds to choose a target.")
				victim = await self._run_vote(lobby, client, wolves_only=True, timeout=60)
				if victim is not None:
					lobby["alive"].discard(victim)
					await lobby["game_channel"].send(f"💀 {lobby['players'][victim].mention} was killed during the night.")
				else:
					await lobby["game_channel"].send("No one was killed during the night.")

				winner = self._winner(lobby)
				if winner:
					break
				lobby["phase"] = "day"
				lobby["used_inspect"].clear()
				await lobby["game_channel"].send("🌞 Day begins. The village has 45 seconds to vote.")
				voted_out = await self._run_vote(lobby, client, wolves_only=False, timeout=45)
				if voted_out is not None:
					lobby["alive"].discard(voted_out)
					role = lobby["roles"][voted_out]
					await lobby["game_channel"].send(
						f"⚖️ {lobby['players'][voted_out].mention} was eliminated and was a **{role}**."
					)
				else:
					await lobby["game_channel"].send("The vote tied or no valid votes were cast. No one was eliminated.")

			winner = self._winner(lobby)
			await lobby["game_channel"].send(
				"🎉 Villagers win!" if winner == "Villagers" else "🐺 Werewolves win!"
			)
			await self._cleanup(lobby)
		except asyncio.CancelledError:
			return
		except (discord.Forbidden, discord.HTTPException) as exc:
			await lobby["game_channel"].send(f"The game stopped because Discord rejected an action: `{exc}`")
			await self._cleanup(lobby)

	async def _run_vote(self, lobby, client, wolves_only, timeout):
		alive_ids = [player_id for player_id in lobby["players"] if player_id in lobby["alive"]]
		if wolves_only:
			targets = [player_id for player_id in alive_ids if lobby["roles"][player_id] != "Werewolf"]
			channel = lobby["wolf_channel"]
		else:
			targets = alive_ids
			channel = lobby["game_channel"]
		if not targets:
			return None

		embed = discord.Embed(
			title="🌙 Werewolf Kill Vote" if wolves_only else "🗳️ Village Vote",
			description="React once to vote. A unique highest vote wins.",
			color=discord.Color.dark_red() if wolves_only else discord.Color.gold(),
		)
		for index, player_id in enumerate(targets):
			embed.add_field(name=VOTE_EMOJIS[index], value=lobby["players"][player_id].display_name, inline=False)
		vote_message = await channel.send(embed=embed)
		for emoji in VOTE_EMOJIS[:len(targets)]:
			await vote_message.add_reaction(emoji)

		await asyncio.sleep(timeout)
		vote_message = await channel.fetch_message(vote_message.id)
		counts = {player_id: 0 for player_id in targets}
		seen_voters = set()
		for reaction in vote_message.reactions:
			if str(reaction.emoji) not in VOTE_EMOJIS[:len(targets)]:
				continue
			target_id = targets[VOTE_EMOJIS.index(str(reaction.emoji))]
			async for user in reaction.users():
				if user.bot or user.id not in lobby["alive"] or user.id in seen_voters:
					continue
				if wolves_only and lobby["roles"].get(user.id) != "Werewolf":
					continue
				counts[target_id] += 1
				seen_voters.add(user.id)

		max_votes = max(counts.values(), default=0)
		leaders = [player_id for player_id, count in counts.items() if count == max_votes and count > 0]
		return leaders[0] if len(leaders) == 1 else None

	def _winner(self, lobby):
		wolves = sum(1 for player_id in lobby["alive"] if lobby["roles"][player_id] == "Werewolf")
		villagers = len(lobby["alive"]) - wolves
		if wolves == 0:
			return "Villagers"
		if wolves >= villagers:
			return "Werewolves"
		return None

	async def _inspect(self, lobby_id, message):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby or not lobby["started"]:
			await self._safe_send(message.channel, content="Active lobby not found.")
			return
		if lobby["phase"] != "day":
			await self._safe_send(message.channel, content="The Aura Seer can inspect only during the day.")
			return
		user_id = message.author.id
		if user_id not in lobby["alive"] or lobby["roles"].get(user_id) != "Aura Seer":
			await self._safe_send(message.channel, content="Only the living Aura Seer can inspect.")
			return
		if user_id in lobby["used_inspect"]:
			await self._safe_send(message.channel, content="You already inspected someone this day.")
			return
		if not message.mentions or message.mentions[0].id not in lobby["alive"]:
			await self._safe_send(message.channel, content="Mention a living player in this lobby.")
			return
		target = message.mentions[0]
		aura = "Bad" if lobby["roles"][target.id] == "Werewolf" else "Good"
		try:
			await message.author.send(f"🔍 {target.display_name}'s aura is **{aura}**.")
		except discord.HTTPException:
			await self._safe_send(message.channel, content="I could not DM you. Enable server-member DMs and try again.")
			return
		lobby["used_inspect"].add(user_id)
		await self._safe_send(message.channel, content=f"✅ {message.author.mention}, inspection complete. Check your DMs.")

	async def _status(self, lobby_id, message):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		lines = []
		for player_id, player in lobby["players"].items():
			state = "Alive" if player_id in lobby["alive"] else ("Dead" if lobby["started"] else "Waiting")
			lines.append(f"• {player.display_name} — {state}")
		embed = discord.Embed(title=f"🐺 Lobby: {lobby_id}", description="\n".join(lines), color=discord.Color.blurple())
		embed.add_field(name="Phase", value=lobby["phase"].title())
		embed.add_field(name="Players", value=f"{len(lobby['players'])}/10")
		await self._safe_send(message.channel, embed=embed)

	async def _end(self, lobby_id, message):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		if message.author.id != lobby["owner_id"] and not message.author.guild_permissions.manage_guild:
			await self._safe_send(message.channel, content="Only the lobby creator or a server manager can end this game.")
			return
		await self._cleanup(lobby, cancel_task=True)
		await self._safe_send(message.channel, content=f"🛑 Lobby `{lobby_id}` ended and cleaned up.")

	async def _cleanup(self, lobby, cancel_task=False):
		task = lobby.get("task")
		if cancel_task and task and task is not asyncio.current_task() and not task.done():
			task.cancel()
		channel = lobby.get("wolf_channel")
		if channel:
			try:
				await channel.delete(reason="Werewolf game ended")
			except (discord.NotFound, discord.Forbidden, discord.HTTPException):
				pass
		LOBBIES.pop((lobby["guild"].id, lobby["id"]), None)
