import asyncio
import io
from urllib.parse import urlparse

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

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
		description = "Generate a meme-style image from an avatar, image URL, or attached image"
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

		image_url = self._get_image_from_message(message, extra_params)
		if not image_url:
			await message.channel.send(
				"Could not find an image. Mention a user, provide an image URL, or attach an image."
			)
			return

		status_message = await message.channel.send("Generating image...")
		image_bytes = await self._download_image(image_url)
		if not image_bytes:
			await status_message.edit(content="I could not fetch that image.")
			return

		try:
			generated_bytes = await asyncio.to_thread(self._render_image, generator_name, image_bytes)
		except Exception:
			await status_message.edit(content="Failed to generate image. Please try again.")
			return

		if not generated_bytes:
			await status_message.edit(content="Failed to generate image. Please try again.")
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
			return target.display_avatar.with_size(512).with_format("png").url

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
					return member.display_avatar.with_size(512).with_format("png").url

		return message.author.display_avatar.with_size(512).with_format("png").url

	def _is_url(self, value):
		try:
			parsed = urlparse(value)
			return parsed.scheme in ("http", "https") and bool(parsed.netloc)
		except ValueError:
			return False

	async def _download_image(self, url):
		timeout = aiohttp.ClientTimeout(total=20)
		async with aiohttp.ClientSession(timeout=timeout) as session:
			try:
				async with session.get(url) as response:
					if response.status != 200:
						return None
					return await response.read()
			except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
				return None

	def _render_image(self, generator_name, image_bytes):
		with Image.open(io.BytesIO(image_bytes)) as source:
			source = source.convert("RGBA")
			base = Image.new("RGBA", (1024, 1024), self._background_color(generator_name))
			canvas = self._apply_style_background(base, generator_name)
			art = self._prepare_art(source, generator_name)
			canvas.alpha_composite(art, (112, 112))
			self._add_frame(canvas, generator_name)
			self._add_overlay(canvas, generator_name)
			self._add_label(canvas, generator_name)

			buffer = io.BytesIO()
			canvas.save(buffer, format="PNG")
			buffer.seek(0)
			return buffer

	def _prepare_art(self, source, generator_name):
		style = ImageOps.fit(source, (800, 800), method=Image.Resampling.LANCZOS)

		if generator_name in {"affect", "rip", "worthless"}:
			style = ImageOps.grayscale(style).convert("RGBA")
		if generator_name in {"beautiful", "bobross", "poutine", "tattoo", "thomas"}:
			style = ImageEnhance.Color(style).enhance(1.3)
			style = ImageEnhance.Contrast(style).enhance(1.15)
		if generator_name in {"delete", "facepalm", "trash"}:
			style = ImageEnhance.Brightness(style).enhance(0.85)
			style = style.filter(ImageFilter.GaussianBlur(radius=1))
		if generator_name in {"challenger", "stonk", "notstonk", "confusedstonk"}:
			style = ImageEnhance.Sharpness(style).enhance(1.8)
			style = ImageEnhance.Contrast(style).enhance(1.2)
		if generator_name in {"jail", "wanted"}:
			style = ImageEnhance.Contrast(style).enhance(1.25)

		return self._rounded_image(style, 32)

	def _rounded_image(self, image, radius):
		mask = Image.new("L", image.size, 0)
		draw = ImageDraw.Draw(mask)
		draw.rounded_rectangle((0, 0, image.size[0] - 1, image.size[1] - 1), radius=radius, fill=255)
		result = Image.new("RGBA", image.size)
		result.paste(image, (0, 0), mask)
		return result

	def _background_color(self, generator_name):
		palette = {
			"ad": (245, 64, 64, 255),
			"affect": (34, 40, 49, 255),
			"beautiful": (255, 240, 200, 255),
			"bobross": (72, 38, 17, 255),
			"challenger": (255, 153, 0, 255),
			"confusedstonk": (32, 74, 135, 255),
			"delete": (77, 22, 22, 255),
			"dexter": (24, 88, 46, 255),
			"facepalm": (30, 30, 30, 255),
			"jail": (45, 48, 71, 255),
			"jokeoverhead": (60, 60, 60, 255),
			"karaba": (113, 48, 162, 255),
			"kyon-gun": (18, 139, 170, 255),
			"mms": (35, 35, 35, 255),
			"notstonk": (19, 73, 72, 255),
			"poutine": (106, 46, 0, 255),
			"rip": (25, 25, 25, 255),
			"shit": (82, 61, 43, 255),
			"stonk": (18, 106, 70, 255),
			"tattoo": (10, 10, 10, 255),
			"thomas": (45, 80, 160, 255),
			"trash": (58, 58, 58, 255),
			"wanted": (185, 137, 74, 255),
			"worthless": (20, 20, 20, 255),
		}
		return palette.get(generator_name, (45, 45, 45, 255))

	def _apply_style_background(self, canvas, generator_name):
		overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
		draw = ImageDraw.Draw(overlay)
		width, height = canvas.size

		for y in range(height):
			alpha = int(90 * (y / height))
			line = Image.new("RGBA", (width, 1), (255, 255, 255, alpha))
			overlay.paste(line, (0, y))

		if generator_name in {"wanted", "poutine", "bobross"}:
			draw.rectangle((40, 40, width - 40, height - 40), outline=(255, 220, 160, 180), width=8)
		if generator_name in {"jail", "delete", "trash"}:
			for x in range(0, width, 48):
				draw.rectangle((x, 0, x + 18, height), fill=(0, 0, 0, 55))

		return Image.alpha_composite(canvas, overlay)

	def _add_frame(self, canvas, generator_name):
		draw = ImageDraw.Draw(canvas)
		width, height = canvas.size
		frame_color = (255, 255, 255, 220)
		if generator_name in {"wanted", "poutine", "bobross"}:
			frame_color = (245, 215, 160, 255)
		elif generator_name in {"jail", "delete", "facepalm"}:
			frame_color = (255, 80, 80, 255)
		elif generator_name in {"stonk", "notstonk", "confusedstonk"}:
			frame_color = (110, 255, 170, 255)

		draw.rounded_rectangle((28, 28, width - 28, height - 28), radius=42, outline=frame_color, width=10)

	def _add_overlay(self, canvas, generator_name):
		draw = ImageDraw.Draw(canvas)
		width, height = canvas.size

		if generator_name == "wanted":
			draw.rectangle((70, 70, width - 70, 170), fill=(90, 55, 20, 220))
			draw.rectangle((70, height - 170, width - 70, height - 70), fill=(90, 55, 20, 220))
		if generator_name == "jail":
			for x in range(0, width, 64):
				draw.rectangle((x, 0, x + 24, height), fill=(0, 0, 0, 95))
		if generator_name == "delete":
			draw.line((120, 120, width - 120, height - 120), fill=(255, 80, 80, 255), width=20)
			draw.line((width - 120, 120, 120, height - 120), fill=(255, 80, 80, 255), width=20)
		if generator_name in {"stonk", "notstonk", "confusedstonk"}:
			arrow_color = (120, 255, 170, 255) if generator_name == "stonk" else (255, 105, 105, 255)
			draw.polygon([(90, 120), (180, 120), (180, 90), (280, 190), (180, 290), (180, 250), (90, 250)], fill=arrow_color)
			if generator_name == "confusedstonk":
				draw.text((width - 320, 120), "?", fill=(255, 255, 255, 255), font=self._font(220))
		if generator_name == "facepalm":
			draw.text((110, height - 210), "FACEPALM", fill=(255, 255, 255, 255), font=self._font(92))
		if generator_name == "rip":
			draw.text((110, 110), "RIP", fill=(255, 255, 255, 255), font=self._font(120))
		if generator_name == "trash":
			draw.text((105, 100), "TRASH", fill=(255, 255, 255, 255), font=self._font(120))
		if generator_name == "worthless":
			draw.text((70, 90), "WORTHLESS", fill=(255, 200, 200, 255), font=self._font(96))

	def _add_label(self, canvas, generator_name):
		draw = ImageDraw.Draw(canvas)
		width, height = canvas.size
		label = generator_name.replace("-", " ").upper()
		font = self._font(84)
		text_bbox = draw.textbbox((0, 0), label, font=font)
		text_width = text_bbox[2] - text_bbox[0]
		text_height = text_bbox[3] - text_bbox[1]
		padding = 26
		x = (width - text_width) // 2
		y = height - text_height - 70

		draw.rounded_rectangle(
			(x - padding, y - padding, x + text_width + padding, y + text_height + padding),
			radius=26,
			fill=(0, 0, 0, 150),
		)
		draw.text((x, y), label, fill=(255, 255, 255, 255), font=font)

	def _font(self, size):
		try:
			return ImageFont.truetype("arial.ttf", size=size)
		except OSError:
			return ImageFont.load_default()
