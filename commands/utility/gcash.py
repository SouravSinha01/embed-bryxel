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
		return (
			f"**{title}**\n"
			f"USD: `${usd_amount:g}` | PHP: `PHP {php_amount:,.2f}`\n"
			f"{detail}"
		)

	def _build_embed(self, title, description, body_lines, author, image_url=None):
		embed = discord.Embed(
			title=title,
			description=description,
			color=discord.Color.from_rgb(39, 174, 96),
		)

		if body_lines:
			embed.add_field(name="Pricing", value="\n\n".join(body_lines), inline=False)

		if image_url:
			embed.set_image(url=image_url)

		embed.set_footer(
			text=f"Requested by {author.display_name}",
			icon_url=author.avatar.url if author.avatar else None,
		)
		return embed

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

		pages = {
			"overview": self._build_embed(
				title="GCash Store Pricing | Bryxel Realm",
				description=(
					"**IMPORTANT:** After paying, open a ticket and attach a screenshot of your payment.\n\n"
					f"**Conversion used:** $1 = PHP {rate:,.2f}\n"
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
				description="Gilded and Radient rank pricing.",
				body_lines=patron_lines,
				author=message.author,
				image_url=GCASH_RANKS_IMAGE_URL,
			),
			"realm_keys": self._build_embed(
				title="Realm Keys",
				description="Realm Key packages and converted PHP values.",
				body_lines=realm_key_lines,
				author=message.author,
				image_url=GCASH_KEYS_IMAGE_URL,
			),
			"everblosson_keys": self._build_embed(
				title="Everblosson Keys (Seasonal)",
				description="Seasonal key packages (same pricing as Realm Keys).",
				body_lines=everblosson_key_lines,
				author=message.author,
				image_url=GCASH_KEYS_IMAGE_URL,
			),
			"relics": self._build_embed(
				title="Bryxel Relic Packages",
				description="Relic packages and converted PHP values.",
				body_lines=relic_lines,
				author=message.author,
				image_url=GCASH_RELICS_IMAGE_URL,
			),
		}

		class PricingSelect(discord.ui.Select):
			def __init__(self):
				options = [
					discord.SelectOption(label="Overview", value="overview", description="Payment steps and important info", emoji="📌"),
					discord.SelectOption(label="Patron Ranks", value="ranks", description="Gilded and Radient pricing", emoji="👑"),
					discord.SelectOption(label="Realm Keys", value="realm_keys", description="7, 15, 32, 64 key packages", emoji="🗝️"),
					discord.SelectOption(label="Everblosson Keys", value="everblosson_keys", description="Seasonal key pricing", emoji="🌸"),
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

		await message.channel.send(embed=pages["overview"], view=view)
