from commands.base_command import BaseCommand
import settings


# This is a convenient command that automatically generates a helpful
# message showing all available commands
class Commands(BaseCommand):
    def __init__(self):
        description = "Displays this help message"
        params = None
        aliases = ["help", "h"]
        category = "Bot"
        super().__init__(description, params, aliases)
        self.category = category

    async def handle(self, params, message, client):
        from message_handler import COMMAND_HANDLERS
        import discord
        from discord.ui import View, Select

        def normalize_token(token):
            return token.strip().lstrip(settings.COMMAND_PREFIX).strip("` ").lower()

        def find_command(token):
            normalized = normalize_token(token)
            for cmd_obj in set(COMMAND_HANDLERS.values()):
                if cmd_obj.name == normalized or normalized in cmd_obj.aliases:
                    return cmd_obj
            return None

        def build_home_embed():
            embed = discord.Embed(
                title="Bryxel Assistant | Help Center",
                description=(
                    "Hey everyone! I'm the Bryxel Assistant, your go-to companion for everything happening in the realm. "
                    "Think of me as the server's digital guidebook-I'm here to make sure you spend less time asking for the IP "
                    "and more time actually building and hanging out."
                ),
                color=discord.Color.from_rgb(46, 204, 113),
            )
            embed.add_field(name="Built With", value="Made in Python", inline=True)
            embed.add_field(name="Made For", value="Made for Bryxel", inline=True)
            embed.add_field(name="Developer", value="<@672695020100386846>", inline=False)
            embed.add_field(
                name="Quick Guide",
                value=f"Use `{settings.COMMAND_PREFIX}<command>` and choose a category from the dropdown below.",
                inline=False,
            )

            if client.user:
                thumb_url = client.user.avatar.url if client.user.avatar else client.user.default_avatar.url
                embed.set_thumbnail(url=thumb_url)

            embed.set_footer(
                text=f"Requested by {message.author.display_name}",
                icon_url=message.author.avatar.url if message.author.avatar else None,
            )
            return embed

        def build_command_embed(cmd_obj):
            usage = f"{settings.COMMAND_PREFIX}{cmd_obj.name}"
            if cmd_obj.params:
                usage += " " + " ".join(f"<{p}>" for p in cmd_obj.params)

            aliases = (
                ", ".join(f"`{settings.COMMAND_PREFIX}{alias}`" for alias in cmd_obj.aliases)
                if cmd_obj.aliases
                else "None"
            )

            embed = discord.Embed(
                title=f"Command Center | {cmd_obj.name}",
                description=getattr(cmd_obj, "summary", cmd_obj.description),
                color=discord.Color.from_rgb(52, 152, 219),
            )
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            embed.add_field(name="Aliases", value=aliases, inline=False)
            embed.add_field(name="Category", value=getattr(cmd_obj, "category", "Other"), inline=True)
            embed.add_field(
                name="Tip",
                value=f"Use `{settings.COMMAND_PREFIX}help` to return to the full command list.",
                inline=False,
            )
            embed.set_footer(
                text=f"Requested by {message.author.display_name}",
                icon_url=message.author.avatar.url if message.author.avatar else None,
            )
            return embed

        def build_category_embed(category_name, command_list):
            embed = discord.Embed(
                title=f"Command Center | {category_name}",
                description=(
                    f"Pick a category from the dropdown below.\n"
                    f"Use `{settings.COMMAND_PREFIX}help <command>` for full command details."
                ),
                color=discord.Color.from_rgb(52, 152, 219),
            )

            for cmd_obj in command_list:
                clean_desc = getattr(cmd_obj, "summary", cmd_obj.description).rstrip(".")

                embed.add_field(
                    name=f"`{settings.COMMAND_PREFIX}{cmd_obj.name}`",
                    value=clean_desc,
                    inline=False,
                )

            embed.set_footer(
                text=(
                    f"{len(command_list)} command(s) in {category_name} | "
                    f"Requested by {message.author.display_name}"
                ),
                icon_url=message.author.avatar.url if message.author.avatar else None,
            )
            return embed

        # Group commands by category
        commands_by_category = {}
        seen_commands = set()
        for name, cmd_obj in sorted(COMMAND_HANDLERS.items()):
            if cmd_obj.name not in seen_commands:
                seen_commands.add(cmd_obj.name)
                cat = getattr(cmd_obj, "category", "Other")
                commands_by_category.setdefault(cat, []).append(cmd_obj)

        # Prepare Select options
        options = [
            discord.SelectOption(label=cat, description=f"Show {cat} commands", value=cat)
            for cat in commands_by_category.keys()
        ]

        class HelpSelect(Select):
            def __init__(self):
                super().__init__(placeholder="Choose a command category...", min_values=1, max_values=1, options=options)

            async def callback(self, interaction):
                cat = self.values[0]
                cmds = commands_by_category[cat]
                embed = build_category_embed(cat, cmds)
                await interaction.response.edit_message(embed=embed, view=self.view)

        if params:
            command_obj = find_command(params[0])
            if command_obj:
                embed = build_command_embed(command_obj)
            else:
                requested_category = params[0].strip()
                if requested_category in commands_by_category:
                    embed = build_category_embed(requested_category, commands_by_category[requested_category])
                else:
                    embed = build_home_embed()
        else:
            embed = build_home_embed()

        view = View()
        view.add_item(HelpSelect())
        await self._safe_send(message.channel, embed=embed, view=view)
