import asyncio
import io
import os
import random
import time
from urllib.parse import urlparse

import aiohttp
import discord

import settings
from commands.base_command import BaseCommand
from commands.image.local_effects_client import LocalEffectsClient
from commands.image.popcat_client import PopcatClient
from rate_limiter import get_global_limiter


POPCAT_AVATAR_GENERATORS = {
	"ad": "ad",
	"blur": "blur",
	"clown": "clown",
	"colorify": "colorify",
	"drip": "drip",
	"greyscale": "greyscale",
	"gun": "gun",
	"hue-rotate": "huerotate",
	"huerotate": "huerotate",
	"invert": "invert",
	"jail": "jail",
	"jokeoverhead": "jokeoverhead",
	"mnm": "mnm",
	"nokia": "nokia",
	"pet": "pet",
	"sadcat": "sadcat",
	"ship": "ship",
	"uncover": "uncover",
	"wanted": "wanted",
}
LOCAL_EFFECTS = {
	"pixel": "pixel",
	"mirror": "mirror",
	"shake": "shake",
	"burn": "burn",
	"mosaic": "mosaic",
	"shatter": "shatter",
}


AVAILABLE_GENERATORS = sorted(
	list(POPCAT_AVATAR_GENERATORS.keys()) + list(LOCAL_EFFECTS.keys())
)


class Generator(BaseCommand):
	COOLDOWN_SECONDS = 15  # Increased from 5s to prevent API spam with multiple concurrent users
	GENERATOR_CAPTIONS = {
		"ad": [
			"{first} just became an ad.",
			"{first} is selling something now.",
			"new ad drop: {first} edition.",
		],
		"blur": [
			"Am I visible, {first}?",
			"{first}, you look a little too hidden.",
			"{first} is fading out of view.",
		],
		"pixel": [
			"{first} got pixelated.",
			"{first} needs more resolution.",
		],
		"clown": [
			"{first} is acting like a clown.",
			"{first} really pulled a clown move.",
		],
		"colorify": [
			"{first} got a color upgrade.",
			"{first} got repainted.",
		],
		"mirror": [
			"{first} meets their reflection.",
			"mirror mirror, which one is {first}?",
		],
		"drip": [
			"{first} is dripping hard.",
			"{first} showed up too clean.",
		],
		"greyscale": [
			"{first} lost the colors.",
			"{first} went full monochrome.",
		],
		"gun": [
			"{first} is armed.",
			"{first} is not to be messed with.",
		],
		"shake": [
			"{first} can't keep still.",
			"{first} is having a moment.",
		],
		"huerotate": [
			"{first} got a hue shift.",
			"{first} got color-rotated.",
		],
		"invert": [
			"{first} got inverted.",
			"{first} turned upside-down on the colors.",
		],
		"jail": [
			"{first} is going to jail.",
			"{first} got caught red-handed.",
		],
		"jokeoverhead": [
			"{first} did not get the joke.",
			"the joke flew right over {first}.",
		],
		"mnm": [
			"{first} got the M&M treatment.",
			"{first} turned into candy.",
		],
		"burn": [
			"{first} is on fire.",
			"too hot to handle: {first}.",
		],
		"nokia": [
			"{first} is on a Nokia screen.",
			"{first} got shrunk to phone size.",
		],
		"mosaic": [
			"{first} went full Roman mosaic.",
			"{first} is art now.",
		],
		"pet": [
			"{first} gets the pet-pet.",
			"{first} is getting head pats.",
		],
		"sadcat": [
			"{first} is now a sad cat.",
			"{first} looks extremely disappointed.",
		],
		"ship": [
			"{first} and {second} are shipped.",
			"{first} x {second} is looking real.",
			"relationship status: {first} + {second}.",
		],
		"shatter": [
			"{first} is shattered.",
			"{first} broke.",
		],
		"uncover": [
			"{first} has been uncovered.",
			"{first} is no longer hiding.",
		],
		"wanted": [
			"{first} is wanted.",
			"wanted poster: {first}.",
		],
	}

	def __init__(self):
		description = "Generate Popcat image edits from an avatar, image URL, or attached image"
		params = []
		aliases = AVAILABLE_GENERATORS + ["gen", "memegen"]
		category = "Image"
		super().__init__(description, params, aliases)
		self.category = category
		self._cooldowns = {}

	async def handle(self, params, message, client):
		cooldown_error = self._check_cooldown(message.author.id)
		if cooldown_error:
			try:
				await message.channel.send(cooldown_error)
			except discord.errors.HTTPException as e:
				if e.status == 429:
					# Hit rate limit on the error message itself, just skip it
					pass
				else:
					raise
			return

		self._mark_cooldown(message.author.id)

		invoked = self._get_invoked_name(message)
		generator_name, extra_params = self._resolve_generator(invoked, params)

		if not generator_name:
			await self._safe_send(
				message.channel,
				content=f"Available: {', '.join(AVAILABLE_GENERATORS)}\n"
				f"Example: `{settings.COMMAND_PREFIX}wanted @user`"
			)
			return

		sadcat_text = None
		if generator_name == "sadcat":
			sadcat_text = self._get_sadcat_text(message, extra_params)
			if not sadcat_text:
				await self._safe_send(
					message.channel,
					content=f"`sadcat` needs text. Example: `{settings.COMMAND_PREFIX}sadcat life is tough`"
				)
				return
			image = ""
		else:
			image = self._get_image_from_message(message, extra_params)
			if not image:
				await self._safe_send(
					message.channel,
					content="Could not find an image. Mention a user, provide an image URL, "
					"or attach an image."
				)
				return

		secondary_image = self._get_secondary_image_for_ship(message, extra_params)
		primary_name = self._resolve_display_name(message, extra_params, fallback_index=0)
		secondary_name = self._resolve_display_name(message, extra_params, fallback_index=1)
		caption = self._build_caption(generator_name, primary_name, secondary_name)
		status_message = await self._safe_send(message.channel, content="Generating image...")
		if not status_message:
			# Rate limited, skip generation
			return
		generated_buffer, error_message = await self._generate(
			generator_name,
			image,
			secondary_image,
			sadcat_text=sadcat_text,
		)
		if not generated_buffer:
			await self._safe_send(
				status_message,
				content=error_message or "Failed to generate image. Please try again in a few moments."
			)
			return

		attachment_name = "attachment.gif" if generator_name == "shake" else "attachment.png"
		file = discord.File(fp=generated_buffer, filename=attachment_name)
		embed = discord.Embed(
			title=caption,
			color=self._get_embed_color(generator_name),
		)
		embed.set_image(url=f"attachment://{attachment_name}")
		embed.set_footer(text=f"Requested by: {message.author.display_name}")
		embed.add_field(name="Generator", value=generator_name, inline=True)
		if generator_name == "ship":
			ship_percentage = random.randint(1, 100)
			ship_bar = self._build_percentage_bar(ship_percentage)
			ship_emoji, ship_text = self._get_ship_result(ship_percentage)
			embed.add_field(
				name=f"Ship Worked {ship_emoji}",
				value=f"{ship_bar} {ship_percentage}% - {ship_text}",
				inline=False,
			)

		try:
			await status_message.delete()
		except (discord.DiscordException, AttributeError):
			pass

		await self._safe_send(message.channel, embed=embed, file=file)

	def _get_invoked_name(self, message):
		content = message.content or ""
		if not content.startswith(settings.COMMAND_PREFIX):
			return ""

		raw = content[len(settings.COMMAND_PREFIX):].strip()
		if not raw:
			return ""

		return raw.split()[0].lower()

	def _resolve_generator(self, invoked_name, params):
		if invoked_name in AVAILABLE_GENERATORS:
			return invoked_name, params

		if not params:
			return None, params

		requested = params[0].strip().lower()
		if requested in AVAILABLE_GENERATORS:
			return requested, params[1:]

		return None, params

	def _get_image_from_message(self, message, params):
		if message.mentions:
			target = message.mentions[0]
			return target.display_avatar.with_size(256).with_format("png").url

		for attachment in message.attachments:
			if attachment.content_type and attachment.content_type.startswith("image/"):
				return attachment.url
			if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
				return attachment.url

		reference = message.reference
		if reference and reference.resolved and hasattr(reference.resolved, "attachments"):
			for attachment in reference.resolved.attachments:
				if attachment.content_type and attachment.content_type.startswith("image/"):
					return attachment.url
				if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
					return attachment.url

		if params:
			first = params[0].strip()
			if self._is_url(first):
				return first
			if first.isdigit() and message.guild:
				member = message.guild.get_member(int(first))
				if member:
					return member.display_avatar.with_size(256).with_format("png").url

		return message.author.display_avatar.with_size(256).with_format("png").url

	def _resolve_display_name(self, message, params, fallback_index=0):
		if len(message.mentions) > fallback_index:
			return message.mentions[fallback_index].display_name

		if len(params) > fallback_index:
			candidate = params[fallback_index].strip()
			if candidate.isdigit() and message.guild:
				member = message.guild.get_member(int(candidate))
				if member:
					return member.display_name

		return message.author.display_name

	def _get_sadcat_text(self, message, params):
		if params:
			return " ".join(p.strip() for p in params if p.strip())

		return None

	def _build_caption(self, generator_name, first_name, second_name):
		variants = self.GENERATOR_CAPTIONS.get(generator_name)
		if variants:
			template = random.choice(variants)
			return template.format(first=first_name, second=second_name)

		return f"Generated for {first_name}."

	def _build_percentage_bar(self, percentage):
		total_slots = 10
		filled_slots = round((percentage / 100) * total_slots)
		return "█" * filled_slots + "░" * (total_slots - filled_slots)

	def _get_ship_result(self, percentage):
		if percentage >= 50:
			return "💖", "strong match"

		if percentage < 10:
			return "💔", "not a match"

		return "💞", "it could go either way"

	def _get_embed_color(self, generator_name):
		palette = {
			"ship": discord.Color.from_rgb(255, 105, 180),
			"wanted": discord.Color.from_rgb(231, 76, 60),
			"jail": discord.Color.from_rgb(155, 89, 182),
			"blur": discord.Color.from_rgb(52, 152, 219),
			"ad": discord.Color.from_rgb(241, 196, 15),
		}
		return palette.get(generator_name, discord.Color.from_rgb(52, 152, 219))

	def _get_secondary_image_for_ship(self, message, params):
		if len(message.mentions) >= 2:
			return message.mentions[1].display_avatar.with_size(256).with_format("png").url

		if len(params) >= 2:
			candidate = params[1].strip()
			if self._is_url(candidate):
				return candidate
			if candidate.isdigit() and message.guild:
				member = message.guild.get_member(int(candidate))
				if member:
					return member.display_avatar.with_size(256).with_format("png").url

		return None

	def _is_url(self, value):
		try:
			parsed = urlparse(value)
			return parsed.scheme in ("http", "https") and bool(parsed.netloc)
		except ValueError:
			return False

	async def _generate(self, generator_name, image, secondary_image=None, sadcat_text=None):
		"""Route local effects to the Pillow client and the rest to Popcat."""
		if generator_name in LOCAL_EFFECTS:
			return await self._generate_local(generator_name, image)

		return await self._generate_with_popcat(
			generator_name,
			image,
			secondary_image,
			sadcat_text=sadcat_text,
		)

	async def _generate_local(self, effect_name: str, image_url: str):
		"""Fetch an image, then apply a local Pillow effect."""
		timeout = aiohttp.ClientTimeout(total=20)
		try:
			async with aiohttp.ClientSession(timeout=timeout) as session:
				async with session.get(image_url) as resp:
					if resp.status != 200:
						return None, "Could not download the image."
					image_bytes = await resp.read()

			client = LocalEffectsClient()
			buffer = await client.generate(effect_name, image_bytes)
			return buffer, None

		except aiohttp.ClientError:
			return None, "Failed to download the image."
		except Exception as exc:
			return None, f"Local effect failed: {exc}"

	async def _generate_with_popcat(self, generator_name, image, secondary_image=None, sadcat_text=None):
		endpoint = POPCAT_AVATAR_GENERATORS.get(generator_name)
		if not endpoint:
			return None, f"`{generator_name}` is not mapped to a Popcat endpoint."

		if endpoint == "ship" and not secondary_image:
			return None, "`ship` requires two users/images. Example: `.ship @user1 @user2`."

		base_url = os.environ.get("POPCAT_BASE_URL", "https://api.popcat.xyz")

		timeout = aiohttp.ClientTimeout(total=40)
		async with aiohttp.ClientSession(timeout=timeout) as session:
			try:
				client = PopcatClient(base_url=base_url, session=session)
				result = await client.generate(
					endpoint,
					image,
					secondary_image_url=secondary_image,
					text_value=sadcat_text,
				)
				buffer = self._to_buffer(result)
				if not buffer:
					return None, "Popcat returned an invalid image payload."

				return buffer, None
			except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
				return None, "Popcat request failed or timed out."
			except RuntimeError as exc:
				return None, f"Popcat error: {exc}"
			except Exception:
				return None, "Popcat generation failed unexpectedly."

	def _to_buffer(self, value):
		if isinstance(value, io.BytesIO):
			value.seek(0)
			return value

		if isinstance(value, (bytes, bytearray)):
			return io.BytesIO(value)

		if hasattr(value, "read"):
			try:
				if hasattr(value, "seek"):
					value.seek(0)
				return value
			except Exception:
				return None

		return None

	def _check_cooldown(self, user_id):
		now = time.monotonic()
		expires_at = self._cooldowns.get(user_id)
		if not expires_at:
			return None

		if now >= expires_at:
			del self._cooldowns[user_id]
			return None

		remaining = expires_at - now
		return f"Please wait {remaining:.1f} seconds before using this command again."

	def _mark_cooldown(self, user_id):
		self._cooldowns[user_id] = time.monotonic() + self.COOLDOWN_SECONDS

	async def _safe_send(self, channel, **kwargs):
		"""Send a message to Discord with 429 error handling.
		
		If hit with a global rate limit (429), returns None without sending.
		Otherwise raises the exception for caller to handle.
		"""
		try:
			# Acquire rate limit token before sending
			await get_global_limiter().acquire()
			return await channel.send(**kwargs)
		except discord.errors.HTTPException as e:
			if e.status == 429:
				# Global rate limit hit - don't retry, just give up
				return None
			raise