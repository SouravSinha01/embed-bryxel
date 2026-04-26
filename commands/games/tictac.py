import asyncio
import random

import discord

import settings
from commands.base_command import BaseCommand


WIN_LINES = (
	(0, 1, 2),
	(3, 4, 5),
	(6, 7, 8),
	(0, 3, 6),
	(1, 4, 7),
	(2, 5, 8),
	(0, 4, 8),
	(2, 4, 6),
)

POSITION_LABELS = {
	0: "A1",
	1: "A2",
	2: "A3",
	3: "B1",
	4: "B2",
	5: "B3",
	6: "C1",
	7: "C2",
	8: "C3",
}

DIFFICULTY_TOKENS = {
	"e": "easy",
	"m": "medium",
	"h": "hard",
	"easy": "easy",
	"medium": "medium",
	"hard": "hard",
}


class Tictac(BaseCommand):
	def __init__(self):
		description = (
			"Play Tic-Tac-Toe: `.ttt @user` for PvP or `.ttt solo e|m|h` for bot mode"
		)
		params = None
		aliases = ["ttt", "tictactoe", "tic"]
		category = "Games"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		if not params:
			await self._send_usage(message)
			return

		first = params[0].strip().lower()
		if first == "solo":
			difficulty = self._parse_solo_difficulty(params[1:])
			if not difficulty:
				await message.channel.send(
					"Invalid solo difficulty. Use `e`, `m`, or `h`.\n"
					f"Example: `{settings.COMMAND_PREFIX}ttt solo h`"
				)
				return

			view = TicTacToeGameView(
				author=message.author,
				opponent=client.user,
				client=client,
				vs_bot=True,
				difficulty=difficulty,
			)
			embed = view.build_embed()
			sent = await message.channel.send(embed=embed, view=view)
			view.message = sent
			return

		opponent = message.mentions[0] if message.mentions else None
		if not opponent:
			await self._send_usage(message)
			return

		if opponent and opponent.id == message.author.id:
			await message.channel.send("You cannot challenge yourself.")
			return

		if opponent and opponent.bot and opponent.id != getattr(client.user, "id", None):
			await message.channel.send("You can challenge a member or play solo against me.")
			return

		if opponent and opponent.id != getattr(client.user, "id", None):
			view = TicTacToeChallengeView(
				author=message.author,
				opponent=opponent,
				client=client,
			)
			embed = view.build_embed()
			sent = await message.channel.send(embed=embed, view=view)
			view.message = sent
			return

		await self._send_usage(message)

	def _parse_solo_difficulty(self, params):
		if not params:
			return None

		token = params[0].strip().lower()
		return DIFFICULTY_TOKENS.get(token)

	async def _send_usage(self, message):
		embed = discord.Embed(
			title="Tic-Tac-Toe Usage",
			description="Use one of the following command formats:",
			color=discord.Color.blurple(),
		)
		embed.add_field(
			name="Play vs Another Player",
			value=f"`{settings.COMMAND_PREFIX}ttt @user`",
			inline=False,
		)
		embed.add_field(
			name="Play Solo vs Bot",
			value=f"`{settings.COMMAND_PREFIX}ttt solo e|m|h`\n`e`=easy, `m`=medium, `h`=hard",
			inline=False,
		)
		embed.set_footer(text="Example: .ttt solo h")
		await message.channel.send(embed=embed)


class TicTacToeChallengeView(discord.ui.View):
	def __init__(self, author, opponent, client):
		super().__init__(timeout=45)
		self.author = author
		self.opponent = opponent
		self.client = client
		self.message = None

	def build_embed(self):
		embed = discord.Embed(
			title="Tic-Tac-Toe Challenge",
			description=(
				f"{self.author.mention} challenged {self.opponent.mention}.\n"
				f"{self.opponent.mention}, click **Accept** to start."
			),
			color=discord.Color.orange(),
		)
		embed.add_field(name="Mode", value="PvP", inline=True)
		embed.add_field(name="Timeout", value="45s", inline=True)
		embed.set_footer(text="X starts first")
		return embed

	@discord.ui.button(label="Accept", style=discord.ButtonStyle.success)
	async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id != self.opponent.id:
			await interaction.response.send_message("Only the challenged player can accept.", ephemeral=True)
			return

		game_view = TicTacToeGameView(
			author=self.author,
			opponent=self.opponent,
			client=self.client,
			vs_bot=False,
			difficulty="medium",
		)
		game_view.message = interaction.message
		await interaction.response.edit_message(embed=game_view.build_embed(), view=game_view)

	@discord.ui.button(label="Decline", style=discord.ButtonStyle.danger)
	async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
		if interaction.user.id not in (self.author.id, self.opponent.id):
			await interaction.response.send_message("Only challenge participants can decline.", ephemeral=True)
			return

		for item in self.children:
			item.disabled = True

		embed = discord.Embed(
			title="Tic-Tac-Toe Challenge",
			description="Challenge declined.",
			color=discord.Color.dark_grey(),
		)
		await interaction.response.edit_message(embed=embed, view=self)

	async def on_timeout(self):
		for item in self.children:
			item.disabled = True

		if self.message:
			embed = discord.Embed(
				title="Tic-Tac-Toe Challenge",
				description="Challenge expired.",
				color=discord.Color.dark_grey(),
			)
			await self.message.edit(embed=embed, view=self)


class TicTacToeCellButton(discord.ui.Button):
	def __init__(self, index):
		super().__init__(label=str(index + 1), style=discord.ButtonStyle.secondary, row=index // 3)
		self.index = index

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, TicTacToeGameView):
			return

		await view.handle_cell_click(interaction, self.index)


class TicTacToeGameView(discord.ui.View):
	def __init__(self, author, opponent, client, vs_bot, difficulty):
		super().__init__(timeout=180)
		self.author = author
		self.opponent = opponent
		self.client = client
		self.vs_bot = vs_bot
		self.difficulty = difficulty
		self.message = None
		self.board = [None] * 9
		self.current_symbol = "X"
		self.last_action = "Game started."
		self.winner_symbol = None
		self.ended = False
		self._lock = asyncio.Lock()

		self.x_player_id = author.id
		self.o_player_id = getattr(opponent, "id", None)

		for index in range(9):
			self.add_item(TicTacToeCellButton(index))

	def build_embed(self):
		status = self._status_text()
		embed = discord.Embed(
			title="Tic-Tac-Toe",
			description=status,
			color=self._embed_color(),
		)

		x_label = f"{self.author.mention} (X - Red)"
		if self.vs_bot:
			o_label = "Bot (O - Green)"
		else:
			o_label = f"{self.opponent.mention} (O - Green)"

		embed.add_field(name="Players", value=f"{x_label}\n{o_label}", inline=True)
		embed.add_field(name="Mode", value="Solo vs Bot" if self.vs_bot else "PvP", inline=True)
		embed.add_field(name="Difficulty", value=self.difficulty.title() if self.vs_bot else "N/A", inline=True)
		embed.add_field(name="Last Move", value=self.last_action, inline=False)
		embed.set_footer(text="Click a tile to play")
		return embed

	def _status_text(self):
		if self.ended:
			if self.winner_symbol == "X":
				return f"Winner: {self.author.mention}"
			if self.winner_symbol == "O":
				return "Winner: Bot" if self.vs_bot else f"Winner: {self.opponent.mention}"
			return "Result: Draw"

		if self.current_symbol == "X":
			return f"Turn: {self.author.mention} (X)"

		return "Turn: Bot (O)" if self.vs_bot else f"Turn: {self.opponent.mention} (O)"

	def _embed_color(self):
		if self.ended:
			if self.winner_symbol == "X":
				return discord.Color.red()
			if self.winner_symbol == "O":
				return discord.Color.green()
			return discord.Color.dark_grey()

		return discord.Color.red() if self.current_symbol == "X" else discord.Color.green()

	def _update_buttons(self):
		for child in self.children:
			if not isinstance(child, TicTacToeCellButton):
				continue

			value = self.board[child.index]
			if value is None:
				child.label = str(child.index + 1)
				child.style = discord.ButtonStyle.secondary
				child.disabled = self.ended
			elif value == "X":
				child.label = "X"
				child.style = discord.ButtonStyle.danger
				child.disabled = True
			else:
				child.label = "O"
				child.style = discord.ButtonStyle.success
				child.disabled = True

		if self.ended:
			for child in self.children:
				child.disabled = True

	async def handle_cell_click(self, interaction: discord.Interaction, index: int):
		async with self._lock:
			if self.ended:
				await interaction.response.send_message("This game has already ended.", ephemeral=True)
				return

			if self.board[index] is not None:
				await interaction.response.send_message("That tile is already taken.", ephemeral=True)
				return

			if not self._is_allowed_player(interaction.user.id):
				await interaction.response.send_message("It is not your turn.", ephemeral=True)
				return

			self.board[index] = self.current_symbol
			actor = self._actor_name_by_symbol(self.current_symbol)
			self.last_action = f"{actor} placed {self.current_symbol} at {POSITION_LABELS[index]}."

			result = self._evaluate_board()
			if result:
				self._end_game(result)
				self._update_buttons()
				await interaction.response.edit_message(embed=self.build_embed(), view=self)
				return

			self.current_symbol = "O" if self.current_symbol == "X" else "X"

			if self.vs_bot and self.current_symbol == "O":
				bot_index = self._pick_bot_move()
				self.board[bot_index] = "O"
				self.last_action = f"Bot placed O at {POSITION_LABELS[bot_index]}."

				result = self._evaluate_board()
				if result:
					self._end_game(result)
				else:
					self.current_symbol = "X"

			self._update_buttons()
			await interaction.response.edit_message(embed=self.build_embed(), view=self)

	def _is_allowed_player(self, user_id):
		if self.current_symbol == "X":
			return user_id == self.x_player_id
		if self.vs_bot:
			return False
		return user_id == self.o_player_id

	def _actor_name_by_symbol(self, symbol):
		if symbol == "X":
			return self.author.display_name
		if self.vs_bot:
			return "Bot"
		return self.opponent.display_name

	def _evaluate_board(self):
		for a, b, c in WIN_LINES:
			if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
				return self.board[a]

		if all(cell is not None for cell in self.board):
			return "draw"

		return None

	def _end_game(self, result):
		self.ended = True
		if result in ("X", "O"):
			self.winner_symbol = result
			winner = self._actor_name_by_symbol(result)
			self.last_action = f"{winner} wins the match."
		else:
			self.winner_symbol = None
			self.last_action = "The board is full. It is a draw."

	def _available_moves(self, board_state=None):
		board_state = board_state if board_state is not None else self.board
		return [idx for idx, value in enumerate(board_state) if value is None]

	def _pick_bot_move(self):
		if self.difficulty == "easy":
			return random.choice(self._available_moves())

		if self.difficulty == "medium":
			if random.random() < 0.65:
				return self._pick_medium_move()
			return random.choice(self._available_moves())

		return self._pick_hard_move()

	def _pick_medium_move(self):
		winning = self._find_winning_move(self.board, "O")
		if winning is not None:
			return winning

		block = self._find_winning_move(self.board, "X")
		if block is not None:
			return block

		if self.board[4] is None:
			return 4

		corners = [idx for idx in (0, 2, 6, 8) if self.board[idx] is None]
		if corners:
			return random.choice(corners)

		return random.choice(self._available_moves())

	def _pick_hard_move(self):
		best_score = -1000
		best_move = None
		for move in self._available_moves():
			trial = self.board.copy()
			trial[move] = "O"
			score = self._minimax(trial, is_bot_turn=False, depth=0)
			if score > best_score:
				best_score = score
				best_move = move

		if best_move is None:
			return random.choice(self._available_moves())

		return best_move

	def _minimax(self, board_state, is_bot_turn, depth):
		result = self._evaluate_board_state(board_state)
		if result == "O":
			return 10 - depth
		if result == "X":
			return depth - 10
		if result == "draw":
			return 0

		moves = self._available_moves(board_state)
		if is_bot_turn:
			best = -1000
			for move in moves:
				next_board = board_state.copy()
				next_board[move] = "O"
				score = self._minimax(next_board, is_bot_turn=False, depth=depth + 1)
				best = max(best, score)
			return best

		best = 1000
		for move in moves:
			next_board = board_state.copy()
			next_board[move] = "X"
			score = self._minimax(next_board, is_bot_turn=True, depth=depth + 1)
			best = min(best, score)
		return best

	def _evaluate_board_state(self, board_state):
		for a, b, c in WIN_LINES:
			if board_state[a] and board_state[a] == board_state[b] == board_state[c]:
				return board_state[a]

		if all(cell is not None for cell in board_state):
			return "draw"

		return None

	def _find_winning_move(self, board_state, symbol):
		for move in self._available_moves(board_state):
			trial = board_state.copy()
			trial[move] = symbol
			if self._evaluate_board_state(trial) == symbol:
				return move
		return None

	async def on_timeout(self):
		self.ended = True
		self.last_action = "Game timed out due to inactivity."
		self._update_buttons()

		if self.message:
			await self.message.edit(embed=self.build_embed(), view=self)
