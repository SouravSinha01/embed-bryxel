from commands.base_command import BaseCommand
import settings


class Warps(BaseCommand):
	def __init__(self):
		description = "Shows the ingame warps menu"
		params = None
		aliases = ["warp",'ark']
		category = "Ingame"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		import discord
		from discord.ui import View, Select

		commands = [
			{
				"key": "warp ark",
				"label": "current ark",
				"usage": "/warp ark",
				"summary": "Teleports you to the current ark.",
				"details": "Current ARK - EverBlosson ark",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495384407509569639/image.png?ex=69e60cc1&is=69e4bb41&hm=fb4eb614cfc328f55ffb858505f1ec62d3a9d1245409e9392a914d0854167444&",
			},
			{
				"key": "warp arkarchive",
				"label": "arkarchive",
				"usage": "/warp arkarchive",
				"summary": "Teleports you to the arkarchive.",
				"details": "Access the arkarchive for previous arks.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495384686053032066/image.png?ex=69e60d04&is=69e4bb84&hm=555be9bdbc15de4d57d1edb88385695938b90a569ad53022622fe6bcf3d6af09&",
			},
			{
				"key": "warp fishing",
				"label": "Fishing",
				"usage": "/warp fishing",
				"summary": "Teleports you to the fishing area.",
				"details": "Access the fishing area for catching fish in Tournaments.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495385010344034375/image.png?ex=69e60d51&is=69e4bbd1&hm=11e9601b0e5822b2e2e89e830b8499d6c866ed96b12191ba10cacb1e61b3f7d5&",
			},
			{
				"key": "warp tavern",
				"label": "tavern",
				"usage": "/warp tavern",
				"summary": "Teleports you to the tavern.",
				"details": "Access the tavern for socializing and earning free AFK money.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495385278842409030/image.png?ex=69e60d91&is=69e4bc11&hm=dcf1a4b6fc9f58d9f4dff52c29b9b641689d325750d343d249e061837a747da9&",
			},
			{
				"key": "warp adept",
				"label": "Adept",
				"usage": "/warp adept",
				"summary": "Teleports you to the Adept for CE's and Transmog orbs.",
				"details": "Gets you to the Adept for CE's and Transmog orbs[Seasonal Key].",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495385514864545872/image.png?ex=69e60dc9&is=69e4bc49&hm=be498858db2e7c6c2b052e4556418dd17e4c95640b3cfb9b6ff30eca13bcb0bb&",
			},
			{
				"key": "warp pvp",
				"label": "PVP",
				"usage": "/warp pvp",
				"summary": "Teleports you to the PVP area.",
				"details": "Access the PVP area for competitive gameplay.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495385927600705617/image.png?ex=69e60e2c&is=69e4bcac&hm=d8cd03840d14de291913996eca01033b45db278f3c66dcab8c166b6c5fdf383c&",
			},
			{
				"key": "warp motm",
				"label": "motm",
				"usage": "/warp motm",
				"summary": "Teleports you to the Merchant of the Month area in /warp market	.",
				"details": "Access to the best selling shop in the game, the Merchant of the Month.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495386457987092502/image.png?ex=69e60eaa&is=69e4bd2a&hm=ed90237852396bbf5e3e35ab7399b2fa65b146e1a5b02f984ec75a886b208402&",
			},
			{
				"key": "warp market",
				"label": "Market",
				"usage": "/warp market",
				"summary": "Teleports you to the market.",
				"details": "Access the market to buy and sell items.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1495387108532293774/image.png?ex=69e60f45&is=69e4bdc5&hm=54e9ffad84951cb3aca6dc34d2d658a0bf66c755bd75e739203d56977e7c1ff8&",
			},
			{
				"key": "warp resource",
				"label": "Resource world ",
				"usage": "/warp resource",
				"summary": "Teleports you to the resource area.",
				"details": "Access the resource area for gathering materials.",
				"image_url": "https://media.discordapp.net/attachments/889695047510011974/1497507081295495188/image.png?ex=69edc5a6&is=69ec7426&hm=3f7f2c6008030f5c4277a1b9c99d0ecd4ee5c83d9cbd06d711783a8d5e4058f7&=&format=webp&quality=lossless&width=1628&height=856",
			}
		]

		command_map = {item["key"]: item for item in commands}
		direct_map = {
			"current ark": "warp ark",
            "ark": "warp ark",
            "arkarchive": "warp arkarchive",
            "fishing": "warp fishing",
            "tavern": "warp tavern",
            "adept": "warp adept",
            "pvp": "warp pvp",
            "motm": "warp motm",
			"market": "warp market",
			"resource": "warp resource",
		}

		def build_home_embed():
			embed = discord.Embed(
				title="Ingame Warps",
				description=(
					f"Select a command from the dropdown for a detailed view.\n"
					f"You can also use `{settings.COMMAND_PREFIX}warp <command>` to jump directly."
				),
				color=discord.Color.from_rgb(88, 101, 242),
			)

			lines = []
			for item in commands:
				lines.append(f"`{item['usage']}`  -  {item['summary']}")

			embed.add_field(name="Available Commands", value="\n".join(lines), inline=False)

			if client.user:
				thumb_url = client.user.avatar.url if client.user.avatar else client.user.default_avatar.url
				embed.set_thumbnail(url=thumb_url)

			embed.set_footer(
				text=f"Requested by {message.author.display_name}",
				icon_url=message.author.avatar.url if message.author.avatar else None,
			)
			return embed

		def build_detail_embed(item):
			embed = discord.Embed(
				title=f"Ingame | {item['label']}",
				description=item["summary"],
				color=discord.Color.from_rgb(46, 204, 113),
			)
			embed.add_field(name="Usage", value=f"`{item['usage']}`", inline=False)
			embed.add_field(name="Details", value=item["details"], inline=False)
			embed.add_field(name="Tip", value=f"Use `{settings.COMMAND_PREFIX}warp` to return to the full list.", inline=False)

			if item.get("image_url"):
				embed.set_image(url=item["image_url"])

			if client.user:
				thumb_url = client.user.avatar.url if client.user.avatar else client.user.default_avatar.url
				embed.set_thumbnail(url=thumb_url)

			embed.set_footer(
				text=f"Requested by {message.author.display_name}",
				icon_url=message.author.avatar.url if message.author.avatar else None,
			)
			return embed

		def resolve_requested_item():
			if not params:
				return None

			joined = " ".join(params[:2]).strip().lower()
			first = params[0].strip().lower()

			if joined in direct_map:
				return command_map.get(direct_map[joined])
			if first in direct_map:
				return command_map.get(direct_map[first])
			if joined in command_map:
				return command_map.get(joined)
			if first in command_map:
				return command_map.get(first)
			return None

		class IngameSelect(Select):
			def __init__(self):
				options = [
					discord.SelectOption(
						label="Overview",
						value="overview",
						description="Return to the ingame warp list",
					)
				]

				for item in commands:
					options.append(
						discord.SelectOption(
							label=item["label"],
							value=item["key"],
							description=item["summary"][:100],
						)
					)

				super().__init__(
					placeholder="Choose an ingame command...",
					min_values=1,
					max_values=1,
					options=options,
				)

			async def callback(self, interaction):
				selected = self.values[0]
				if selected == "overview":
					embed = build_home_embed()
				else:
					embed = build_detail_embed(command_map[selected])

				await interaction.response.edit_message(embed=embed, view=self.view)

		view = View()
		view.add_item(IngameSelect())

		requested_item = resolve_requested_item()
		if requested_item:
			embed = build_detail_embed(requested_item)
		else:
			embed = build_home_embed()

		await self._safe_send(message.channel, embed=embed, view=view)

