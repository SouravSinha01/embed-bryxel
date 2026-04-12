from commands.base_command import BaseCommand
import settings


class Igm(BaseCommand):
	def __init__(self):
		description = "Shows the ingame command menu"
		params = None
		aliases = ["ingame"]
		category = "Ingame"
		super().__init__(description, params, aliases)
		self.category = category

	async def handle(self, params, message, client):
		import discord
		from discord.ui import View, Select

		commands = [
			{
				"key": "chatcolor gui",
				"label": "ChatColor GUI",
				"usage": "/chatcolor gui",
				"summary": "Open the chat color and formatting GUI.",
				"details": "Use the GUI to pick colors and style your chat quickly.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558374322176192/image.png?ex=69dbc4ce&is=69da734e&hm=f8c6f617e6af546cb10af118e1f2f69b9ee91def18861f7e162395b837e1a111&",
			},
			{
				"key": "fancyglow",
				"label": "Fancy Glow",
				"usage": "/fancyglow",
				"summary": "Open the FancyGlow feature.",
				"details": "Access the glow-related feature or menu for this command.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558819098624010/image.png?ex=69dbc538&is=69da73b8&hm=6436f5e9bb26859c3ad27449c5be40fcb06a880621cca740acc5924a9083dffa&",
			},
			{
				"key": "cosmetics",
				"label": "Cosmetics",
				"usage": "/cosmetics",
				"summary": "Open the cosmetics menu.",
				"details": "View and manage cosmetic options available in-game.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492558992017199324/image.png?ex=69dbc562&is=69da73e2&hm=bc963436684bfcd4f8f835d22a323bc1467095606a92e9b9001ea08cf191102c&",
			},
			{
				"key": "shop",
				"label": "Shop",
				"usage": "/shop",
				"summary": "Open the in-game shop.",
				"details": "Jump into the shop interface to browse items and services.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492559182245658795/image.png?ex=69dbc58f&is=69da740f&hm=9d6787d23909e382880316c72c0800e86c1cc0d66a7784b847e76409746d5f45&",
			},
			{
				"key": "bp",
				"label": "BP",
				"usage": "/bp",
				"summary": "Open the BP menu.",
				"details": "Open the BP command menu or interface in-game.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492559388290842666/image.png?ex=69dbc5c0&is=69da7440&hm=1f743347199f2b81d744e41312275335bfb98bbbfc890541c9d6fd55b0c95b4c&",
			},
			{
				"key": "goose",
				"label": "Goose",
				"usage": "/goose",
				"summary": "Open the Goose feature.",
				"details": "Access the Goose rewards for daily weekly rewards.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492560122717933778/image.png?ex=69dbc66f&is=69da74ef&hm=bb4bf1b4e764d29bda9c521ec1c131268c54791a5983c0464469fa23aded7a05&",
			},
			{
				"key": "bryxelpop",
				"label": "BryxelPop",
				"usage": "/bryxelpop",
				"summary": "Open the BryxelPop feature.",
				"details": "Launch the BryxelPop command or its related interface.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492561645535494224/image.png?ex=69dbc7da&is=69da765a&hm=008aa76825c28c1a53ebcaf40f7013696b7d1cca3d29b4af742570c16076aec3&",
			},
			{
				"key": "settlement",
				"label": "Settlement",
				"usage": "/settlement",
				"summary": "Open the settlement menu.",
				"details": "View settlement-related info -Comabat Advancement Ranks.",
				"image_url": "https://cdn.discordapp.com/attachments/889695047510011974/1492561855644962816/image.png?ex=69dbc80c&is=69da768c&hm=069506bf258d26dfd1de18686b965432ff5b217b7b60766be4caf82ec8103431&",
			},
		]

		command_map = {item["key"]: item for item in commands}
		direct_map = {
			"chatcolor": "chatcolor gui",
			"chatcolor gui": "chatcolor gui",
			"fancyglow": "fancyglow",
			"cosmetics": "cosmetics",
			"shop": "shop",
			"bp": "bp",
			"goose": "goose",
			"bryxelpop": "bryxelpop",
			"settlement": "settlement",
		}

		def build_home_embed():
			embed = discord.Embed(
				title="Ingame Commands",
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
						description="Return to the ingame command list",
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
