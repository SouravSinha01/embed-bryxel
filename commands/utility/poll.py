from commands.base_command import BaseCommand
import discord
import settings


class Poll(BaseCommand):
	def __init__(self):
		description = (
			"Create an interactive poll with vote buttons and an optional timeout. "
			"Example: .poll Best feature? | Help menu | Polls | Events"
		)
		params = ["question", "option1 | option2 | option3", "duration=30m(optional)"]
		aliases = ["votepoll", "survey"]
		category = "Utility"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		if not params:
			embed = discord.Embed(
				title="📊 Create a Poll",
				description=(
					"Use `|` to separate the question and options.\n"
					f"Example: `{settings.COMMAND_PREFIX}poll Best feature? | Help menu | Polls | Events | duration=10m`"
				),
				color=discord.Color.blurple(),
			)
			embed.add_field(
				name="Format",
				value=f"`{settings.COMMAND_PREFIX}poll Question | Option 1 | Option 2 [| duration=10m]`",
				inline=False,
			)
			embed.set_footer(text="You need at least 2 options to start a poll.")
			await message.channel.send(embed=embed)
			return

		raw_content = message.content[len(settings.COMMAND_PREFIX) :].strip()
		command_part = raw_content.split(maxsplit=1)
		if len(command_part) < 2:
			await message.channel.send(
				f"Usage: `{settings.COMMAND_PREFIX}poll Question | Option 1 | Option 2 [| duration=10m]`"
			)
			return

		payload = command_part[1].strip()
		segments = [segment.strip() for segment in payload.split("|") if segment.strip()]
		if len(segments) < 3:
			await message.channel.send(
				"Please provide a question and at least 2 options using `|` separators.\n"
				f"Example: `{settings.COMMAND_PREFIX}poll Best feature? | Help menu | Polls | Events`"
			)
			return

		duration_seconds = 1800
		last_segment = segments[-1].lower()
		if last_segment.startswith(("duration=", "time=")):
			duration_value = last_segment.split("=", 1)[1].strip()
			parsed_duration = self._parse_duration(duration_value)
			if parsed_duration is None:
				await message.channel.send(
					"Invalid duration. Use values like `30s`, `10m`, `2h`, or `1d`."
				)
				return
			duration_seconds = parsed_duration
			segments = segments[:-1]

		question = segments[0]
		options = segments[1:]

		if len(options) < 2:
			await message.channel.send("Please provide at least two poll options.")
			return

		if len(options) > 10:
			await message.channel.send("Please keep polls to 10 options or fewer.")
			return

		if len(question) > 256:
			await message.channel.send("Poll question is too long. Keep it under 256 characters.")
			return

		for option in options:
			if len(option) > 80:
				await message.channel.send(
					f"Option too long: `{option[:40]}...`\nKeep each option under 80 characters."
				)
				return

		poll_view = PollView(
			question=question,
			options=options,
			author=message.author,
			duration_seconds=duration_seconds,
			client=client,
		)
		embed = poll_view.build_embed(active=True)
		sent_message = await message.channel.send(embed=embed, view=poll_view)
		poll_view.message = sent_message

	def _parse_duration(self, value):
		value = value.strip().lower()
		if not value:
			return None

		number_part = ""
		unit_part = ""
		for char in value:
			if char.isdigit():
				number_part += char
			else:
				unit_part += char

		if not number_part or not unit_part:
			return None

		amount = int(number_part)
		unit_part = unit_part.strip()

		if unit_part == "s":
			return amount
		if unit_part == "m":
			return amount * 60
		if unit_part == "h":
			return amount * 3600
		if unit_part == "d":
			return amount * 86400
		return None


class PollButton(discord.ui.Button):
	def __init__(self, index, label):
		super().__init__(
			label=label,
			style=discord.ButtonStyle.primary,
			row=index // 5,
		)
		self.index = index

	async def callback(self, interaction: discord.Interaction):
		view = self.view
		if not isinstance(view, PollView):
			return
		await view.handle_vote(interaction, self.index)


class PollView(discord.ui.View):
	def __init__(self, question, options, author, duration_seconds, client):
		super().__init__(timeout=duration_seconds)
		self.question = question
		self.options = options
		self.author = author
		self.client = client
		self.message = None
		self.votes = [0 for _ in options]
		self.voters = {}
		self.closed = False

		for index, option in enumerate(options):
			self.add_item(PollButton(index, self._shorten_label(option)))

	def _shorten_label(self, text):
		return text if len(text) <= 80 else text[:77] + "..."

	def build_embed(self, active=True):
		total_votes = sum(self.votes)
		title = "📊 Poll"
		color = discord.Color.green() if active else discord.Color.dark_grey()
		embed = discord.Embed(title=title, description=self.question, color=color)

		if total_votes == 0:
			lines = ["No votes yet."]
		else:
			lines = []
			for index, option in enumerate(self.options):
				votes = self.votes[index]
				percent = (votes / total_votes) * 100 if total_votes else 0
				bar = self._progress_bar(percent)
				lines.append(f"`{index + 1}.` {option}\n{bar} **{votes}** vote(s) - **{percent:.1f}%**")

		embed.add_field(name="Results", value="\n\n".join(lines), inline=False)
		embed.add_field(name="Total Votes", value=str(total_votes), inline=True)
		embed.add_field(name="Status", value="Open" if active else "Closed", inline=True)
		embed.set_footer(text=f"Created by {self.author.display_name}")

		if self.client.user:
			thumb_url = self.client.user.avatar.url if self.client.user.avatar else self.client.user.default_avatar.url
			embed.set_thumbnail(url=thumb_url)

		return embed

	def _progress_bar(self, percent):
		filled = int(round(percent / 10))
		filled = max(0, min(10, filled))
		return "▰" * filled + "▱" * (10 - filled)

	async def handle_vote(self, interaction: discord.Interaction, option_index: int):
		if self.closed:
			await interaction.response.send_message("This poll is closed.", ephemeral=True)
			return

		user_id = interaction.user.id
		previous_vote = self.voters.get(user_id)

		if previous_vote == option_index:
			self.votes[option_index] -= 1
			del self.voters[user_id]
		else:
			if previous_vote is not None:
				self.votes[previous_vote] -= 1
			self.votes[option_index] += 1
			self.voters[user_id] = option_index

		await interaction.response.edit_message(embed=self.build_embed(active=True), view=self)

	async def on_timeout(self):
		self.closed = True
		for item in self.children:
			item.disabled = True

		if self.message:
			await self.message.edit(embed=self.build_embed(active=False), view=self)
