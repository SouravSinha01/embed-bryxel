import asyncio
import io
import os
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
	"achievement": "achievement",
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
TEXT_GENERATORS = {"achievement", "sadcat"}


AVAILABLE_GENERATORS = sorted(
	list(POPCAT_AVATAR_GENERATORS.keys()) + list(LOCAL_EFFECTS.keys())
)


class Generator(BaseCommand):
	COOLDOWN_SECONDS = 15  # Increased from 5s to prevent API spam with multiple concurrent users
	def __init__(self):
		description = "Generate Popcat image edits from an avatar, image URL, or attached image"
		params = []
		aliases = AVAILABLE_GENERATORS + ["gen", "memegen"]
		category = "Image"
		super().__init__(description, params, aliases)
		self.category = category
		self._cooldowns = {}

	async def handle(self, params, message, client):
		invoked = self._get_invoked_name(message)
		generator_name, extra_params = self._resolve_generator(invoked, params)
		if not generator_name:
			await self._safe_send(message.channel, embed=self._build_help_embed())
			return

		cooldown_error = self._check_cooldown(message.author.id)
		if cooldown_error:
			try:
				await self._safe_send(message.channel, content=cooldown_error)
			except discord.errors.HTTPException as e:
				if e.status == 429:
					# Hit rate limit on the error message itself, just skip it
					pass
				else:
					raise
			return

		text_value = None
		if generator_name in TEXT_GENERATORS:
			text_value = self._get_text_from_params(extra_params)
			if not text_value:
				example = "Built a castle" if generator_name == "achievement" else "life is tough"
				await self._safe_send(
					message.channel,
					content=f"`{generator_name}` needs text. Example: `{settings.COMMAND_PREFIX}{generator_name} {example}`"
				)
				return
			if generator_name == "achievement" and len(text_value) > 60:
				await self._safe_send(message.channel, content="Achievement text must be 60 characters or fewer.")
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

		self._mark_cooldown(message.author.id)

		secondary_image = self._get_secondary_image_for_ship(message, extra_params)
		status_message = await self._safe_send(message.channel, content="Generating image...")
		if not status_message:
			# Rate limited, skip generation
			return
		generated_buffer, error_message = await self._generate(
			generator_name,
			image,
			secondary_image,
			text_value=text_value,
		)
		if not generated_buffer:
			reason = error_message or "Failed to generate image. Please try again in a few moments."
			print(f"Image generation failed for {generator_name}: {reason}", flush=True)
			await status_message.edit(content=reason)
			return

		attachment_name = f"generated.{self._image_extension(generated_buffer)}"
		file = discord.File(fp=generated_buffer, filename=attachment_name)
		await status_message.edit(content=None, attachments=[file])

	def _build_help_embed(self):
		embed = discord.Embed(
			title="Image Generator",
			description=f"`{settings.COMMAND_PREFIX}gen <effect> [@user | image URL | text]`",
			color=discord.Color.from_rgb(52, 152, 219),
		)
		embed.add_field(
			name="Image effects",
			value=", ".join(f"`{name}`" for name in AVAILABLE_GENERATORS if name not in TEXT_GENERATORS and name != "hue-rotate"),
			inline=False,
		)
		embed.add_field(
			name="Text effects",
			value=", ".join(f"`{name}`" for name in sorted(TEXT_GENERATORS)),
			inline=False,
		)
		embed.add_field(
			name="Examples",
			value=(
				f"`{settings.COMMAND_PREFIX}gen wanted @user`\n"
				f"`{settings.COMMAND_PREFIX}gen achievement Built a castle`\n"
				f"`{settings.COMMAND_PREFIX}ship @user1 @user2`"
			),
			inline=False,
		)
		return embed

	@staticmethod
	def _image_extension(buffer):
		position = buffer.tell()
		try:
			buffer.seek(0)
			header = buffer.read(12)
		finally:
			buffer.seek(position)
		if header.startswith((b"GIF87a", b"GIF89a")):
			return "gif"
		if header.startswith(b"\xff\xd8\xff"):
			return "jpg"
		if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
			return "webp"
		return "png"

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

	def _get_text_from_params(self, params):
		if params:
			return " ".join(p.strip() for p in params if p.strip())

		return None

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

	async def _generate(self, generator_name, image, secondary_image=None, text_value=None):
		"""Route local effects to the Pillow client and the rest to Popcat."""
		if generator_name in LOCAL_EFFECTS:
			return await self._generate_local(generator_name, image)

		return await self._generate_with_popcat(
			generator_name,
			image,
			secondary_image,
			text_value=text_value,
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

	async def _generate_with_popcat(self, generator_name, image, secondary_image=None, text_value=None):
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
					text_value=text_value,
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
