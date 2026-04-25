import discord
from commands.base_command import BaseCommand


USD_TO_PHP_RATE = 60.70
GCASH_QR_IMAGE_URL = "https://cdn.discordapp.com/attachments/889695047510011974/1497415147302555803/image.png?ex=69ed7007&is=69ec1e87&hm=cc9d6d2c3349858cc1de8c569cc582dc8636d2b51c75a2f37bce329b5b49be21&"
GCASH_RANKS_IMAGE_URL = "https://cdn.discordapp.com/attachments/889695047510011974/1497419716460023918/ChatGPT_Image_Apr_25_2026_07_40_58_AM.png?ex=69ed7449&is=69ec22c9&hm=88d9870919b5093235cc475b1b29ea3b7fe31183752f77c54fd65f9eb8841ae8&"
GCASH_KEYS_IMAGE_URL = "https://media.discordapp.net/attachments/889695047510011974/1497420680906543257/content.png?ex=69ed752f&is=69ec23af&hm=9e7482f7299e27515aa93b258179a69f7123d607365bb1f2e0e32367b82dcdb5&=&format=webp&quality=lossless&width=1376&height=917"
GCASH_RELICS_IMAGE_URL = "https://media.discordapp.net/attachments/889695047510011974/1497420882740772954/content.png?ex=69ed755f&is=69ec23df&hm=90ca5d411b6ecad243ef0bf4f4fdde5fa394aaf8a8c7c9fb2d77b79acabeec67&=&format=webp&quality=lossless&width=960&height=960"


class Gcash(BaseCommand):

	def __init__(self):
		description = "Shows GCash payment pricing for Bryxel store items"
		params = None
		aliases = ["pay", "payment", "gcashpay"]
		category = "Utility"
		super().__init__(description, params, aliases)
		self.category = category

	@staticmethod
	def _usd_to_php(usd_amount):
		return usd_amount * USD_TO_PHP_RATE

	@classmethod
	def _format_line(cls, title, usd_amount, detail):
		php_amount = cls._usd_to_php(usd_amount)
		return f"• **{title}** - ${usd_amount:g} (~PHP {php_amount:,.2f})\\n  {detail}"

	async def handle(self, params, message, client):
		rate = USD_TO_PHP_RATE

		patron_lines = [
			self._format_line("Gilded Rank", 10, "Patron Rank"),
			self._format_line("Radient Rank", 10, "Patron Rank"),
		]

		key_pricing = [
			(2, 7),
			(4, 15),
			(6, 32),
			(8, 64),
		]

		realm_key_lines = [
			self._format_line(f"${usd:g} Package", usd, f"{amount} Realm Keys")
			for usd, amount in key_pricing
		]

		everblosson_key_lines = [
			self._format_line(f"${usd:g} Package", usd, f"{amount} Everblosson Keys")
			for usd, amount in key_pricing
		]

		relic_lines = [
			self._format_line("Starter Relics", 0.5, "50 Relics"),
			self._format_line("Basic Relics", 1, "100 Relics"),
			self._format_line("Hunter Relics", 5, "500 Relics"),
			self._format_line("Collector Relics", 10, "1000 Relics"),
		]

		embed = discord.Embed(
			title="GCash Store Pricing | Bryxel Realm",
			description=(
				"**IMPORTANT: After paying, open a ticket and attach a screenshot of your payment.**\n\n"
				"Base prizes and conversion guide for GCash payments.\\n"
				f"**Conversion used:** $1 = PHP {rate:,.2f}"
			),
			color=discord.Color.from_rgb(39, 174, 96)
		)

		embed.add_field(name="Patron Ranks", value="\\n\\n".join(patron_lines), inline=False)
		embed.add_field(name="Realm Keys", value="\\n\\n".join(realm_key_lines), inline=False)
		embed.add_field(name="Everblosson Keys (Seasonal)", value="\\n\\n".join(everblosson_key_lines), inline=False)
		embed.add_field(name="Bryxel Relic Packages", value="\\n\\n".join(relic_lines), inline=False)
		embed.add_field(
			name="After Payment (Important)",
			value=(
				"Open a support ticket right away and send a **screenshot** of your GCash payment "
				"so staff can verify and deliver your package faster."
			),
			inline=False,
		)
		embed.add_field(
			name="How to Pay via GCash",
			value=(
				"1. Pick your package from the list above.\\n"
				"2. Scan the GCash QR code.\\n"
				"3. Open a ticket and send your payment screenshot for processing."
			),
			inline=False,
		)

		if GCASH_QR_IMAGE_URL:
			embed.set_image(url=GCASH_QR_IMAGE_URL)

		embed.set_footer(
			text=f"Requested by {message.author.display_name}",
			icon_url=message.author.avatar.url if message.author.avatar else None,
		)

		embeds_to_send = [embed]

		optional_image_sections = [
			("Patron Rank Preview", GCASH_RANKS_IMAGE_URL, "Preview for Gilded and Radient ranks."),
			("Keys Preview", GCASH_KEYS_IMAGE_URL, "Preview for Realm Keys and Everblosson Keys."),
			("Relics Preview", GCASH_RELICS_IMAGE_URL, "Preview for Bryxel Relic packages."),
		]

		for title, image_url, description in optional_image_sections:
			if not image_url:
				continue

			preview_embed = discord.Embed(
				title=title,
				description=description,
				color=discord.Color.from_rgb(46, 204, 113),
			)
			preview_embed.set_image(url=image_url)
			embeds_to_send.append(preview_embed)

		view = discord.ui.View()
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

		await message.channel.send(embeds=embeds_to_send, view=view)
