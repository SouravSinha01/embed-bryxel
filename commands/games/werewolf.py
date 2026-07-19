import asyncio
import random

import discord

import settings
from commands.base_command import BaseCommand


VOTE_EMOJIS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")
LOBBIES = {}
ROLE_LIMITS = {
	"wolves": (1, 3),
	"protectors": (0, 2),
	"seers": (0, 2),
}


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
		if action in {"info", "help", "rules"}:
			await self._send_help(message)
			return

		lobby_id = params[1].lower() if len(params) > 1 else None
		if action not in {"create", "join", "config", "start", "inspect", "status", "end"}:
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
		elif action == "config":
			await self._config(lobby_id, message, client)
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
			title="🐺 Werewolf: How to Play",
			description=(
				"Werewolf is a hidden-role social deduction game. The village is trying to find the "
				"Werewolves before the Werewolves become powerful enough to take over."
			),
			color=discord.Color.dark_red(),
		)
		embed.add_field(
			name="Start a Game",
			value=(
				f"`{prefix}ww create <lobby>` - create a lobby and join it\n"
				f"`{prefix}ww join <lobby>` - join before the game starts\n"
				f"`{prefix}ww config <lobby>` - open the role setup menu\n"
				f"`{prefix}ww start <lobby>` - start with the current setup"
			),
			inline=False,
		)
		embed.add_field(
			name="Config Menu",
			value=(
				"The lobby creator can set Werewolves, Protectors, and Aura Seers from one message. "
				"`Auto Balance` picks a fair setup for the current player count, and `Start Game` starts from the panel."
			),
			inline=False,
		)
		embed.add_field(
			name="Roles",
			value=(
				"**Werewolf** - secretly votes by DM at night to kill a non-wolf.\n"
				"**Protector** - chooses one living player by DM to protect at night.\n"
				"**Aura Seer** - chooses one living player by DM and learns if their aura is Good or Bad.\n"
				"**Villager** - has no night power, but votes during the day."
			),
			inline=False,
		)
		embed.add_field(
			name="Game Flow",
			value=(
				"1. The bot DMs everyone their secret role.\n"
				"2. Night begins: Werewolves, Protectors, and Aura Seers act privately by DM.\n"
				"3. The bot announces whether someone died or survived.\n"
				"4. Day begins: living players discuss and vote publicly.\n"
				"5. Repeat until one team wins."
			),
			inline=False,
		)
		embed.add_field(
			name="Winning",
			value=(
				"Villagers win when all Werewolves are eliminated.\n"
				"Werewolves win when living Werewolves are equal to or greater than the other living players."
			),
			inline=False,
		)
		embed.add_field(
			name="Other Commands",
			value=(
				f"`{prefix}ww status <lobby>` - show players, phase, and setup\n"
				f"`{prefix}ww end <lobby>` - end and clean up the lobby\n"
				f"`{prefix}ww info` - show this guide"
			),
			inline=False,
		)
		embed.set_footer(text="4-10 players. Secret actions use DMs, so admins cannot peek through hidden channels.")
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
			"config": {"auto": True, "wolves": 1, "protectors": 1, "seers": 0},
			"phase": "setup",
			"started": False,
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

	async def _config(self, lobby_id, message, client):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		if lobby["started"]:
			await self._safe_send(message.channel, content="That game has already started.")
			return
		if message.author.id != lobby["owner_id"]:
			await self._safe_send(message.channel, content="Only the lobby creator can configure the game.")
			return

		self._ensure_config(lobby)
		view = WerewolfConfigView(command=self, lobby=lobby, author=message.author, client=client)
		sent = await self._safe_send(message.channel, embed=view.build_embed(), view=view)
		view.message = sent

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

		error = await self._start_lobby(lobby, message.channel, client)
		if error:
			await self._safe_send(message.channel, content=error)

	async def _start_lobby(self, lobby, channel, client):
		valid, reason, config, villagers = self._validate_config(lobby)
		if not valid:
			return reason

		lobby_id = lobby["id"]
		players = list(lobby["players"].values())
		role_names = self._build_roles(config, villagers)
		random.shuffle(role_names)
		lobby["roles"] = {player.id: role for player, role in zip(players, role_names)}
		lobby["alive"] = set(lobby["players"])
		lobby["started"] = True
		lobby["phase"] = "starting"

		wolf_ids = [player_id for player_id, role in lobby["roles"].items() if role == "Werewolf"]
		try:
			for player in players:
				role = lobby["roles"][player.id]
				content = f"🐺 Your role in lobby `{lobby_id}` is **{role}**."
				if role == "Werewolf":
					fellow_wolves = [
						lobby["players"][player_id].display_name
						for player_id in wolf_ids
						if player_id != player.id
					]
					if fellow_wolves:
						content += f"\nYour fellow Werewolves: {', '.join(fellow_wolves)}."
					content += "\nYour kill target list will arrive here by DM each night."
				await player.send(content)
		except discord.HTTPException:
			lobby["started"] = False
			lobby["phase"] = "setup"
			return "I could not DM every player. Everyone must enable server-member DMs before starting."

		counts = {name: role_names.count(name) for name in set(role_names)}
		await self._safe_send(
			channel,
			content=(f"🌙 Werewolf started in `{lobby_id}` with {len(players)} players. "
					 f"Roles: {', '.join(f'{count} {name}' for name, count in sorted(counts.items()))}.\n"
					 "All night actions arrive by DM."),
		)
		lobby["task"] = asyncio.create_task(self._game_loop(lobby, client))
		return None

	def _default_config(self, player_count):
		return {
			"auto": True,
			"wolves": 2 if player_count >= 8 else 1,
			"protectors": 1 if player_count >= 4 else 0,
			"seers": 1 if player_count >= 6 else 0,
		}

	def _ensure_config(self, lobby):
		if "config" not in lobby:
			lobby["config"] = self._default_config(len(lobby["players"]))

	def _effective_config(self, lobby):
		self._ensure_config(lobby)
		if lobby["config"].get("auto", True):
			return self._default_config(len(lobby["players"]))
		return {
			"auto": False,
			"wolves": int(lobby["config"].get("wolves", 1)),
			"protectors": int(lobby["config"].get("protectors", 0)),
			"seers": int(lobby["config"].get("seers", 0)),
		}

	def _validate_config(self, lobby):
		config = self._effective_config(lobby)
		player_count = len(lobby["players"])
		if player_count < 4:
			return False, "At least 4 players are required.", config, 0
		if player_count > len(VOTE_EMOJIS):
			return False, "This lobby is full (10 players maximum).", config, 0

		for key, (minimum, maximum) in ROLE_LIMITS.items():
			count = config[key]
			if count < minimum or count > maximum:
				return False, f"{key.title()} must be between {minimum} and {maximum}.", config, 0

		non_wolves = player_count - config["wolves"]
		if config["wolves"] >= non_wolves:
			return False, "Werewolves must be fewer than the non-wolf players.", config, 0

		villagers = player_count - config["wolves"] - config["protectors"] - config["seers"]
		if villagers < 1:
			return False, "The setup needs at least 1 Villager.", config, villagers

		return True, "Valid setup.", config, villagers

	def _build_roles(self, config, villagers):
		return (["Werewolf"] * config["wolves"] + ["Protector"] * config["protectors"]
				+ ["Aura Seer"] * config["seers"] + ["Villager"] * villagers)

	def build_config_embed(self, lobby):
		valid, reason, config, villagers = self._validate_config(lobby)
		player_count = len(lobby["players"])
		mode = "Auto balance" if config.get("auto") else "Custom"
		status = "Valid" if valid else f"Invalid: {reason}"
		color = discord.Color.green() if valid else discord.Color.orange()
		embed = discord.Embed(
			title=f"🐺 Werewolf Config: {lobby['id']}",
			description="Use the menus below to tune the setup before starting.",
			color=color,
		)
		embed.add_field(name="Players", value=f"{player_count}/10", inline=True)
		embed.add_field(name="Mode", value=mode, inline=True)
		embed.add_field(name="Status", value=status, inline=False)
		embed.add_field(name="Werewolves", value=str(config["wolves"]), inline=True)
		embed.add_field(name="Protectors", value=str(config["protectors"]), inline=True)
		embed.add_field(name="Aura Seers", value=str(config["seers"]), inline=True)
		embed.add_field(name="Villagers", value=str(max(0, villagers)), inline=True)
		embed.set_footer(text="Only the lobby creator can use this panel.")
		return embed

	async def _game_loop(self, lobby, client):
		try:
			while self._winner(lobby) is None:
				lobby["phase"] = "night"
				await lobby["game_channel"].send(
					"🌙 Night falls. Werewolves, Protector, and Aura Seer have 60 seconds to act."
				)
				victim, protected_targets = await self._run_night(lobby, timeout=60)
				if victim is not None and victim in protected_targets:
					await lobby["game_channel"].send("🛡️ Someone was attacked during the night, but survived.")
				elif victim is not None:
					lobby["alive"].discard(victim)
					await lobby["game_channel"].send(f"💀 {lobby['players'][victim].mention} was killed during the night.")
				else:
					await lobby["game_channel"].send("No one was killed during the night.")

				winner = self._winner(lobby)
				if winner:
					break
				lobby["phase"] = "day"
				await lobby["game_channel"].send("🌞 Day begins. The village has 45 seconds to vote.")
				voted_out = await self._run_vote(lobby, timeout=45)
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

	async def _run_night(self, lobby, timeout):
		living_wolves = self._living_role_ids(lobby, "Werewolf")
		living_protectors = self._living_role_ids(lobby, "Protector")
		living_seers = self._living_role_ids(lobby, "Aura Seer")
		living_ids = self._living_ids(lobby)

		wolf_targets = [player_id for player_id in living_ids if lobby["roles"][player_id] != "Werewolf"]
		tasks = {
			"victim": asyncio.create_task(
				self._collect_wolf_kill(lobby, wolf_targets, living_wolves, timeout)
			)
		}

		if living_protectors:
			tasks["protected"] = asyncio.create_task(
				self._collect_protections(lobby, living_ids, living_protectors, timeout)
			)

		if living_seers:
			tasks["inspections"] = asyncio.create_task(self._run_seer_inspections(lobby, living_ids, living_seers, timeout))

		results = await asyncio.gather(*tasks.values(), return_exceptions=True)
		night = dict(zip(tasks.keys(), results))

		if isinstance(night.get("victim"), Exception):
			raise night["victim"]
		if isinstance(night.get("protected"), Exception):
			await self._safe_send(lobby["game_channel"], content="I could not collect the Protector's action tonight.")
			night["protected"] = set()
		if isinstance(night.get("inspections"), Exception):
			await self._safe_send(lobby["game_channel"], content="I could not collect the Aura Seer's inspection tonight.")
			night["inspections"] = None

		return night.get("victim"), night.get("protected") or set()

	async def _collect_protections(self, lobby, targets, living_protectors, timeout):
		if not targets or not living_protectors:
			return set()

		tasks = []
		for protector_id in living_protectors:
			protector = lobby["players"][protector_id]
			tasks.append(
				asyncio.create_task(
					self._run_target_prompt(
						lobby=lobby,
						channel=protector.dm_channel or await protector.create_dm(),
						title="🛡️ Protector Action",
						description="React once to protect one living player tonight.",
						targets=targets,
						timeout=timeout,
						valid_voter_ids={protector_id},
						result_mode="single",
					)
				)
			)

		results = await asyncio.gather(*tasks, return_exceptions=True)
		return {result for result in results if not isinstance(result, Exception) and result is not None}

	async def _run_seer_inspections(self, lobby, living_ids, living_seers, timeout):
		tasks = {}
		for seer_id in living_seers:
			targets = [player_id for player_id in living_ids if player_id != seer_id]
			if not targets:
				continue
			seer = lobby["players"][seer_id]
			tasks[seer_id] = asyncio.create_task(
				self._run_target_prompt(
					lobby=lobby,
					channel=seer.dm_channel or await seer.create_dm(),
					title="🔍 Aura Seer Inspection",
					description="React once to inspect one living player's aura tonight.",
					targets=targets,
					timeout=timeout,
					valid_voter_ids={seer_id},
					result_mode="single",
				)
			)

		if not tasks:
			return None

		results = await asyncio.gather(*tasks.values(), return_exceptions=True)
		for seer_id, result in zip(tasks.keys(), results):
			if isinstance(result, Exception) or result is None:
				continue
			aura = "Bad" if lobby["roles"][result] == "Werewolf" else "Good"
			await lobby["players"][seer_id].send(f"🔍 {lobby['players'][result].display_name}'s aura is **{aura}**.")
		return None

	async def _collect_wolf_kill(self, lobby, targets, living_wolves, timeout):
		if not targets or not living_wolves:
			return None

		tasks = []
		for wolf_id in living_wolves:
			wolf = lobby["players"][wolf_id]
			tasks.append(
				asyncio.create_task(
					self._run_target_prompt(
						lobby=lobby,
						channel=wolf.dm_channel or await wolf.create_dm(),
						title="🌙 Werewolf Kill Vote",
						description="React once to choose tonight's victim.",
						targets=targets,
						timeout=timeout,
						valid_voter_ids={wolf_id},
						result_mode="single",
						color=discord.Color.dark_red(),
					)
				)
			)

		results = await asyncio.gather(*tasks, return_exceptions=True)
		counts = {}
		for result in results:
			if isinstance(result, Exception) or result is None:
				continue
			counts[result] = counts.get(result, 0) + 1

		max_votes = max(counts.values(), default=0)
		leaders = [player_id for player_id, count in counts.items() if count == max_votes and count > 0]
		return leaders[0] if len(leaders) == 1 else None

	async def _run_vote(self, lobby, timeout):
		alive_ids = [player_id for player_id in lobby["players"] if player_id in lobby["alive"]]
		targets = alive_ids
		channel = lobby["game_channel"]
		if not targets:
			return None
		return await self._run_target_prompt(
			lobby=lobby,
			channel=channel,
			title="🗳️ Village Vote",
			description="React once to vote. A unique highest vote wins.",
			targets=targets,
			timeout=timeout,
			valid_voter_ids=set(alive_ids),
			result_mode="vote",
			color=discord.Color.gold(),
		)

	async def _run_target_prompt(
		self,
		lobby,
		channel,
		title,
		description,
		targets,
		timeout,
		valid_voter_ids,
		result_mode,
		color=None,
	):
		if not targets or not valid_voter_ids:
			return None

		embed = discord.Embed(
			title=title,
			description=description,
			color=color or discord.Color.blurple(),
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
				if user.bot or user.id not in valid_voter_ids or user.id not in lobby["alive"] or user.id in seen_voters:
					continue
				counts[target_id] += 1
				seen_voters.add(user.id)

		if result_mode == "single":
			for target_id, count in counts.items():
				if count > 0:
					return target_id
			return None

		max_votes = max(counts.values(), default=0)
		leaders = [player_id for player_id, count in counts.items() if count == max_votes and count > 0]
		return leaders[0] if len(leaders) == 1 else None

	def _living_ids(self, lobby):
		return [player_id for player_id in lobby["players"] if player_id in lobby["alive"]]

	def _living_role_ids(self, lobby, role):
		return [player_id for player_id in self._living_ids(lobby) if lobby["roles"].get(player_id) == role]

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
		await self._safe_send(
			message.channel,
			content="Aura Seer inspections now happen automatically by private DM during the night phase.",
		)

	async def _status(self, lobby_id, message):
		lobby = LOBBIES.get((message.guild.id, lobby_id))
		if not lobby:
			await self._safe_send(message.channel, content="Lobby not found.")
			return
		self._ensure_config(lobby)
		lines = []
		for player_id, player in lobby["players"].items():
			state = "Alive" if player_id in lobby["alive"] else ("Dead" if lobby["started"] else "Waiting")
			lines.append(f"• {player.display_name} — {state}")
		embed = discord.Embed(title=f"🐺 Lobby: {lobby_id}", description="\n".join(lines), color=discord.Color.blurple())
		valid, reason, config, villagers = self._validate_config(lobby)
		embed.add_field(name="Phase", value=lobby["phase"].title())
		embed.add_field(name="Players", value=f"{len(lobby['players'])}/10")
		embed.add_field(
			name="Setup",
			value=(
				f"Wolves: {config['wolves']} | Protectors: {config['protectors']} | "
				f"Seers: {config['seers']} | Villagers: {max(0, villagers)}"
			),
			inline=False,
		)
		embed.add_field(name="Config", value="Valid" if valid else reason, inline=False)
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
		LOBBIES.pop((lobby["guild"].id, lobby["id"]), None)


class WerewolfRoleSelect(discord.ui.Select):
	def __init__(self, role_key, label, current_value, row):
		minimum, maximum = ROLE_LIMITS[role_key]
		options = []
		for count in range(minimum, maximum + 1):
			options.append(
				discord.SelectOption(
					label=f"{label}: {count}",
					value=str(count),
					default=count == current_value,
				)
			)
		super().__init__(
			placeholder=f"Set {label}",
			min_values=1,
			max_values=1,
			options=options,
			row=row,
		)
		self.role_key = role_key

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, WerewolfConfigView):
			return
		if not await view.authorize(interaction):
			return
		if view.lobby["started"]:
			await interaction.response.send_message("That game has already started.", ephemeral=True)
			return

		view.command._ensure_config(view.lobby)
		view.lobby["config"]["auto"] = False
		view.lobby["config"][self.role_key] = int(self.values[0])
		view.rebuild_items()
		await interaction.response.edit_message(embed=view.build_embed(), view=view)


class WerewolfAutoButton(discord.ui.Button):
	def __init__(self):
		super().__init__(label="Auto Balance", style=discord.ButtonStyle.secondary, row=3)

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, WerewolfConfigView):
			return
		if not await view.authorize(interaction):
			return
		if view.lobby["started"]:
			await interaction.response.send_message("That game has already started.", ephemeral=True)
			return

		view.lobby["config"] = view.command._default_config(len(view.lobby["players"]))
		view.rebuild_items()
		await interaction.response.edit_message(embed=view.build_embed(), view=view)


class WerewolfStartButton(discord.ui.Button):
	def __init__(self):
		super().__init__(label="Start Game", style=discord.ButtonStyle.success, row=3)

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, WerewolfConfigView):
			return
		if not await view.authorize(interaction):
			return
		if view.lobby["started"]:
			await interaction.response.send_message("That game has already started.", ephemeral=True)
			return

		await interaction.response.defer()
		error = await view.command._start_lobby(view.lobby, interaction.channel, view.client)
		if error:
			await interaction.followup.send(error, ephemeral=True)
			return

		view.disable_all_items()
		await interaction.message.edit(embed=view.build_embed(), view=view)


class WerewolfCloseButton(discord.ui.Button):
	def __init__(self):
		super().__init__(label="Close", style=discord.ButtonStyle.danger, row=3)

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, WerewolfConfigView):
			return
		if not await view.authorize(interaction):
			return

		view.disable_all_items()
		await interaction.response.edit_message(embed=view.build_embed(), view=view)


class WerewolfConfigView(discord.ui.View):
	def __init__(self, command, lobby, author, client):
		super().__init__(timeout=300)
		self.command = command
		self.lobby = lobby
		self.author = author
		self.client = client
		self.message = None
		self.rebuild_items()

	def rebuild_items(self):
		self.clear_items()
		config = self.command._effective_config(self.lobby)
		self.add_item(WerewolfRoleSelect("wolves", "Werewolves", config["wolves"], row=0))
		self.add_item(WerewolfRoleSelect("protectors", "Protectors", config["protectors"], row=1))
		self.add_item(WerewolfRoleSelect("seers", "Aura Seers", config["seers"], row=2))
		self.add_item(WerewolfAutoButton())
		self.add_item(WerewolfStartButton())
		self.add_item(WerewolfCloseButton())

	def build_embed(self):
		return self.command.build_config_embed(self.lobby)

	async def authorize(self, interaction):
		if interaction.user.id == self.lobby["owner_id"]:
			return True
		await interaction.response.send_message("Only the lobby creator can use this panel.", ephemeral=True)
		return False

	def disable_all_items(self):
		for item in self.children:
			item.disabled = True

	async def on_timeout(self):
		self.disable_all_items()
		if self.message:
			await self.message.edit(embed=self.build_embed(), view=self)
