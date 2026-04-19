from commands.base_command import BaseCommand
import settings


class Igm(BaseCommand):
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
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558374322176192/image.png?ex=69dbc4ce&is=69da734e&hm=f8c6f617e6af546cb10af118e1f2f69b9ee91def18861f7e162395b837e1a111&",
			},
			{
				"key": "warp arkarchive",
				"label": "arkarchive",
				"usage": "/warp arkarchive",
				"summary": "Teleports you to the arkarchive.",
				"details": "Access the arkarchive for previous arks.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558819098624010/image.png?ex=69dbc538&is=69da73b8&hm=6436f5e9bb26859c3ad27449c5be40fcb06a880621cca740acc5924a9083dffa&",
			},
			{
				"key": "warp fishing",
				"label": "Fishing",
				"usage": "/warp fishing",
				"summary": "Teleports you to the fishing area.",
				"details": "Access the fishing area for catching fish in Tournaments.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558992017199324/image.png?ex=69dbc562&is=69da73e2&hm=bc963436684bfcd4f8f835d22a323bc1467095606a92e9b9001ea08cf191102c&",
			},
			{
				"key": "warp tavern",
				"label": "tavern",
				"usage": "/warp tavern",
				"summary": "Teleports you to the tavern.",
				"details": "Access the tavern for socializing and earning free AFK money.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492559182245658795/image.png?ex=69dbc58f&is=69da740f&hm=9d6787d23909e382880316c72c0800e86c1cc0d66a7784b847e76409746d5f45&",
			},
			{
				"key": "warp adept",
				"label": "Adept",
				"usage": "/warp adept",
				"summary": "Teleports you to the Adept for CE's and Transmog orbs.",
				"details": "Gets you to the Adept for CE's and Transmog orbs[Seasonal Key].",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492559388290842666/image.png?ex=69dbc5c0&is=69da7440&hm=1f743347199f2b81d744e41312275335bfb98bbbfc890541c9d6fd55b0c95b4c&",
			},
			{
				"key": "warp pvp",
				"label": "PVP",
				"usage": "/warp pvp",
				"summary": "Teleports you to the PVP area.",
				"details": "Access the PVP area for competitive gameplay.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492560122717933778/image.png?ex=69dbc66f&is=69da74ef&hm=bb4bf1b4e764d29bda9c521ec1c131268c54791a5983c0464469fa23aded7a05&",
			},
			{
				"key": "warp motm",
				"label": "motm",
				"usage": "/warp motm",
				"summary": "Teleports you to the Merchant of the Month area.",
				"details": "Access to the best selling shop in the game, the Merchant of the Month.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492561645535494224/image.png?ex=69dbc7da&is=69da765a&hm=008aa76825c28c1a53ebcaf40f7013696b7d1cca3d29b4af742570c16076aec3&",
			},
			
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
		}

		def build_home_embed():
			embed = discord.Embed(
				title="Ingame Warps",
				description=(
					f"Select a command from the dropdown for a detailed view.\n"
					f"You can also use `{settings.COMMAND_PREFIX}igm <command>` to jump directly."
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
			embed.add_field(name="Tip", value=f"Use `{settings.COMMAND_PREFIX}igm` to return to the full list.", inline=False)

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

		await message.channel.send(embed=embed, view=view)

