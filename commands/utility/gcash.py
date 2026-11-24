import asyncio
import math
import time
from datetime import datetime, timezone

import aiohttp
import discord
from commands.base_command import BaseCommand


USD_TO_PHP_RATE_URL = "https://api.exchangerate.fun/latest?base=USD"
RATE_REFRESH_SECONDS = 60 * 60
RATE_RETRY_SECONDS = 5 * 60
GCASH_QR_IMAGE_URL = "https://cdn.discordapp.com/attachments/889695047510011974/1497415147302555803/image.png?ex=69ed7007&is=69ec1e87&hm=cc9d6d2c3349858cc1de8c569cc582dc8636d2b51c75a2f37bce329b5b49be21&"
GCASH_RANKS_IMAGE_URL = "https://cdn.discordapp.com/attachments/889695047510011974/1497419716460023918/ChatGPT_Image_Apr_25_2026_07_40_58_AM.png?ex=69ed7449&is=69ec22c9&hm=88d9870919b5093235cc475b1b29ea3b7fe31183752f77c54fd65f9eb8841ae8&"
GCASH_SEASONAL_ARK_IMAGE_URL = "https://media.discordapp.net/attachments/987911480362016769/1574646651245559938/2c8aa7d4-7c5b-473a-8399-c0649493f96a.png?ex=6b066779&is=6b0515f9&hm=d4744c2d4f4509ae1c6a2441a2f1a46be0faf3cc41392641a0f6a81635ca39d2&format=webp&quality=lossless&width=1280&height=1049"
GCASH_SPECIAL_ARK_IMAGE_URL = "https://cdn.discordapp.com/attachments/987911480362016769/1574649296593362984/66842f81-7688-460a-b4ad-422c1278d193.png?ex=6b0669ef&is=6b05186f&hm=2434887876835cadaecdf16978c28468cac3331d7860a20c39021873462f9fa5&"
GCASH_RELICS_IMAGE_URL = "https://media.discordapp.net/attachments/889695047510011974/1497420882740772954/content.png?ex=69ed755f&is=69ec23df&hm=90ca5d411b6ecad243ef0bf4f4fdde5fa394aaf8a8c7c9fb2d77b79acabeec67&=&format=webp&quality=lossless&width=960&height=960"


class Gcash(BaseCommand):

	def __init__(self):
		description = "Shows GCash payment pricing for Bryxel store items"
		params = None
		aliases = ["pay", "payment", "gcashpay"]
		category = "Utility"
		super().__init__(description, params, aliases)
		self.category = category
		self._rate = None
		self._rate_date = None
		self._rate_stale = False
		self._next_rate_fetch = 0
		self._rate_lock = asyncio.Lock()

	@staticmethod
	def _parse_rate(data):
		if not isinstance(data, dict):
			raise ValueError("Invalid exchange-rate response")
		if data.get("base") != "USD":
			raise ValueError("Unexpected exchange-rate currency pair")
		rate = float(data["rates"]["PHP"])
		if not math.isfinite(rate) or rate <= 0:
			raise ValueError("Invalid USD/PHP exchange rate")
		rate_date = datetime.fromtimestamp(int(data["timestamp"]), timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
		return rate, rate_date

	async def _get_rate(self):
		async with self._rate_lock:
			if time.monotonic() < self._next_rate_fetch:
				return self._rate, self._rate_date, self._rate_stale

			try:
				timeout = aiohttp.ClientTimeout(total=8)
				async with aiohttp.ClientSession(timeout=timeout) as session:
					async with session.get(USD_TO_PHP_RATE_URL) as response:
						response.raise_for_status()
						data = await response.json()
				self._rate, self._rate_date = self._parse_rate(data)
				self._rate_stale = False
				self._next_rate_fetch = time.monotonic() + RATE_REFRESH_SECONDS
			except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, TypeError, ValueError) as exc:
				print(f"Could not refresh USD/PHP rate: {exc}", flush=True)
				self._rate_stale = True
				self._next_rate_fetch = time.monotonic() + RATE_RETRY_SECONDS

			return self._rate, self._rate_date, self._rate_stale

	@staticmethod
	def _format_line(title, usd_amount, detail, rate):
		php_amount = usd_amount * rate
		return (
			f"**{title}**\n"
			f"USD: `${usd_amount:g}`\n"
			f"PHP estimate: `PHP {php_amount:,.2f}`\n"
			f"{detail}"
		)

	def _build_embed(self, title, description, body_lines, author, image_url=None, columns=False):
		embed = discord.Embed(
			title=title,
			description=description,
			color=discord.Color.from_rgb(39, 174, 96),
		)

		if body_lines:
			if columns:
				for index, line in enumerate(body_lines):
					item_title, item_details = line.split("\n", 1)
					embed.add_field(name=item_title.strip("*"), value=item_details, inline=True)
					if index % 2 == 1 and index < len(body_lines) - 1:
						embed.add_field(name="\u200b", value="\u200b", inline=True)
			else:
				embed.add_field(name="Payment steps", value="\n".join(body_lines), inline=False)

		if image_url:
			embed.set_image(url=image_url)

		embed.set_footer(
			text=f"Requested by {author.display_name}",
			icon_url=author.avatar.url if author.avatar else None,
		)
		return embed

	async def handle(self, params, message, client):
		rate, rate_date, rate_stale = await self._get_rate()
		if rate is None:
			await self._safe_send(
				message.channel,
				content="GCash pricing is temporarily unavailable because the USD/PHP rate could not be fetched. Please try again soon.",
			)
			return

		patron_lines = [
			self._format_line("Gilded Rank", 10, "Patron Rank", rate),
			self._format_line("Radient Rank", 10, "Patron Rank", rate),
		]

		key_pricing = [
			(2, 8),
			(4, 16),
			(6, 32),
			(8, 64),
		]

		special_ark_key_lines = [
			self._format_line(f"$**{usd:g}** Package", usd, f"**{amount}** Special ARK Keys", rate)
			for usd, amount in key_pricing
		]

		seasonal_ark_key_lines = [
			self._format_line(f"$**{usd:g}** Package", usd, f"**{amount}** Seasonal ARK Keys", rate)
			for usd, amount in key_pricing
		]

		relic_lines = [
			self._format_line("Starter Relics", 0.5, "**50 Relics**", rate),
			self._format_line("Basic Relics", 1, "**100 Relics**", rate),
			self._format_line("Hunter Relics", 5, "**500 Relics**", rate),
			self._format_line("Collector Relics", 10, "**1000 Relics**", rate),
		]
		rate_note = f"**USD/PHP market rate:** $1 = PHP {rate:,.4f} (ExchangeRate.fun, {rate_date})\n"
		if rate_stale:
			rate_note += "**Last available rate; confirm the PHP amount before paying.**\n"

		pages = {
			"overview": self._build_embed(
				title="GCash Store Pricing | Bryxel Realm",
				description=(
					"**IMPORTANT:** After paying, open a ticket and attach a screenshot of your payment.\n\n"
					f"{rate_note}\n\n"
					"**PHP amounts are estimates; market and payment rates may differ wrt Global Prices, Check Once!**.\n\n"
					"Use the dropdown menu below to view pricing per category."
				),
				body_lines=[
					"1. Choose your item category from the dropdown.",
					"2. Scan and pay using the GCash QR.",
					"3. Open a ticket and send payment screenshot.",
				],
				author=message.author,
				image_url=GCASH_QR_IMAGE_URL,
			),
			"ranks": self._build_embed(
				title="Patron Ranks",
				description="Gilded and Radient rank pricing. Please note you can rank up to Radiant after getting Gilded",
				body_lines=patron_lines,
				author=message.author,
				image_url=GCASH_RANKS_IMAGE_URL,
				columns=True,
			),
			"special_ark_keys": self._build_embed(
				title="Special ARK Keys",
				description="Special ARK key packages and converted PHP values.",
				body_lines=special_ark_key_lines,
				author=message.author,
				image_url=GCASH_SPECIAL_ARK_IMAGE_URL,
				columns=True,
			),
			"seasonal_ark_keys": self._build_embed(
				title="Seasonal ARK Keys",
				description="Seasonal ARK key packages and converted PHP values.",
				body_lines=seasonal_ark_key_lines,
				author=message.author,
				image_url=GCASH_SEASONAL_ARK_IMAGE_URL,
				columns=True,
			),
			"relics": self._build_embed(
				title="Bryxel Relic Packages",
				description="Relic packages and converted PHP values.",
				body_lines=relic_lines,
				author=message.author,
				image_url=GCASH_RELICS_IMAGE_URL,
				columns=True,
			),
		}

		class PricingSelect(discord.ui.Select):
			def __init__(self):
				options = [
					discord.SelectOption(label="Overview", value="overview", description="Payment steps and important info", emoji="📌"),
					discord.SelectOption(label="Patron Ranks", value="ranks", description="Gilded and Radient pricing", emoji="👑"),
					discord.SelectOption(label="Special ARK Keys", value="special_ark_keys", description="Special ARK key pricing", emoji="🗝️"),
					discord.SelectOption(label="Seasonal ARK Keys", value="seasonal_ark_keys", description="Seasonal ARK key pricing", emoji="🌸"),
					discord.SelectOption(label="Relic Packages", value="relics", description="50 to 1000 relic bundles", emoji="🧿"),
				]
				super().__init__(
					placeholder="Select a pricing category...",
					min_values=1,
					max_values=1,
					options=options,
				)

			async def callback(self, interaction):
				selected_page = self.values[0]
				await interaction.response.edit_message(embed=pages[selected_page], view=self.view)

		view = discord.ui.View(timeout=300)
		view.add_item(PricingSelect())
		view.add_item(discord.ui.Button(
			label="Open Webshop",
			style=discord.ButtonStyle.link,
			url="https://bryxel-realm.tebex.io/",
			emoji="🛒",
		))
		view.add_item(discord.ui.Button(
			label="Open Website",
			style=discord.ButtonStyle.link,
			url="https://bryxelrealm.github.io/BryxelRealm.com/",
			emoji="🌐",
		))

		await self._safe_send(message.channel, embed=pages["overview"], view=view)
