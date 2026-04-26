import asyncio
import os
from urllib.parse import urlparse

import aiohttp
import discord

import settings
from commands.base_command import BaseCommand


AVAILABLE_GENERATORS = [
	"ad",
	"affect",
	"beautiful",
	"bobross",
	"challenger",
	"confusedstonk",
	"delete",
	"dexter",
	"facepalm",
	"hitler",
	"jail",
	"jokeoverhead",
	"karaba",
	"kyon-gun",
	"mms",
	"notstonk",
	"poutine",
	"rip",
	"shit",
	"stonk",
	"tattoo",
	"thomas",
	"trash",
	"wanted",
	"worthless",
]


class Generator(BaseCommand):
	def __init__(self):
		description = "Generate a meme image from an avatar, image URL, or attached image"
		params = ["name(optional)", "@user | image_url(optional)"]
		aliases = AVAILABLE_GENERATORS + ["gen", "memegen"]
		category = "Image"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		invoked = self._get_invoked_name(message)
		generator_name, extra_params = self._resolve_generator(invoked, params)

		if not generator_name:
			examples = (
				f"`{settings.COMMAND_PREFIX}generator wanted @user`\n"
				f"`{settings.COMMAND_PREFIX}generator ad https://example.com/image.png`\n"
				f"`{settings.COMMAND_PREFIX}ad @user`"
			)
			await message.channel.send(
				"Please provide a valid generator name.\n"
				f"Available: {', '.join(AVAILABLE_GENERATORS)}\n\n"
				f"Examples:\n{examples}"
			)
			return

		image = self._get_image_from_message(message, extra_params)
		if not image:
			await message.channel.send(
				"Could not find an image. Mention a user, provide an image URL, "
				"or attach an image."
			)
			return

		api_key = os.environ.get("STRANGE_API_KEY")
		if not api_key:
			await message.channel.send(
				"Missing `STRANGE_API_KEY` in environment variables."
			)
			return

		base_api = os.environ.get("IMAGE_BASE_API") or os.environ.get("IMAGE_BASE_API_URL")
		if not base_api:
			await message.channel.send(
				"Missing `IMAGE_BASE_API` or `IMAGE_BASE_API_URL` in environment variables."
			)
			return

		endpoint = self._get_generator_url(base_api, generator_name, image)

		status_message = await message.channel.send("Generating image...")
		generated_bytes = await self._fetch_buffer(endpoint, api_key)
		if not generated_bytes:
			await status_message.edit(
				content="Failed to generate image. Please try again in a few moments."
			)
			return

		file = discord.File(fp=generated_bytes, filename="attachment.png")
		embed = discord.Embed(color=discord.Color.from_rgb(52, 152, 219))
		embed.set_image(url="attachment://attachment.png")
		embed.set_footer(text=f"Requested by: {message.author.display_name}")
		embed.add_field(name="Generator", value=generator_name, inline=True)

		try:
			await status_message.delete()
		except discord.DiscordException:
			pass

		await message.channel.send(embed=embed, file=file)

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

	def _is_url(self, value):
		try:
			parsed = urlparse(value)
			return parsed.scheme in ("http", "https") and bool(parsed.netloc)
		except ValueError:
			return False

	def _get_generator_url(self, base_api, generator_name, image):
		from urllib.parse import urlencode

		query = urlencode({"image": image})
		return f"{base_api.rstrip('/')}/generators/{generator_name}?{query}"

	async def _fetch_buffer(self, url, api_key):
		headers = {
			"Authorization": f"Bearer {api_key}",
		}

		timeout = aiohttp.ClientTimeout(total=25)
		async with aiohttp.ClientSession(timeout=timeout) as session:
			try:
				async with session.get(url, headers=headers) as response:
					if response.status != 200:
						return None
					return await response.read()
			except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
				return None
