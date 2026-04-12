import discord
from commands.base_command import BaseCommand

TICKET_CHANNEL_ID = 1255158325591670844

class Ticket(BaseCommand):
    def __init__(self):
        description = "Shows a step-by-step guide on how to open a support ticket"
        params = None
        aliases = ["guide"]
        category = "Utility"
        super().__init__(description, params, aliases)
        self.category = category


    async def handle(self, params, message, client):
        """Display the ticket guide with pagination"""
        
        # Create guide pages
        pages = [
            self._create_intro_page(),
            self._create_step1_page(),
            self._create_step2_page(),
            self._create_step3_page(),
            self._create_step4_page(),
            self._create_final_page(),
        ]
        
        current_page = 0
        
        # Send the initial message with the first page
        guide_msg = await message.channel.send(embed=pages[current_page], 
                                               view=PaginatorView(pages, current_page, message.author.id))

    def _create_intro_page(self):
        embed = discord.Embed(
            title="🎫 How to Open a Support Ticket",
            description="Welcome! This guide will walk you through the process of opening a support ticket in Bryxel.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="What is a Support Ticket?",
            value="A ticket allows you to get help from our support team with issues, problems, or questions. "
                  "Each ticket is private and handled individually.",
            inline=False
        )
        embed.add_field(
            name="This guide has:",
            value="📖 6 easy steps\n⏱️ Takes about 2 minutes\n✅ Then you're ready!",
            inline=False
        )
        embed.set_footer(text="Page 1 of 6 • Use the buttons below to navigate")
        return embed

    def _create_step1_page(self):
        embed = discord.Embed(
            title="Step 1: Find the Ticket Channel",
            description="First, locate the ticket channel in your server.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📍 Location",
            value=f"Look for the ticket channel in your server sidebar (Channel ID: `{TICKET_CHANNEL_ID}`)\n\n"
                  "It might be labeled as **#ticket** in Support Category.",
            inline=False
        )
        embed.add_field(
            name="💡 Tip",
            value="Check the channel description for any specific instructions.",
            inline=False
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1489128952889872454/image.png?ex=69cf4ae9&is=69cdf969&hm=ca18e99bd3688a25fb4598293b892325d208fbf7d8bdb270881ee38c20e459aa&")
        embed.set_footer(text="Page 2 of 6 • Use the buttons below to navigate")
        return embed

    def _create_step2_page(self):
        embed = discord.Embed(
            title="Step 2: Look for the Ticket Bot Message",
            description="In the ticket channel, find the message from the ticket bot.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🔍 What to look for",
            value="There should be a message with buttons or reactions that says something like:\n"
                  "• 'Click to create a ticket'\n"
                  "• 'Open Support Ticket'\n"
                  "• Or similar wording",
            inline=False
        )
        embed.add_field(
            name="📌 Note",
            value="This message is usually pinned or at the top of the channel.",
            inline=False
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1489129524850327572/image.png?ex=69cf4b71&is=69cdf9f1&hm=3808c9bf0e4c807c51153ae9b6b9afa39686b23680775401bf1fa24dcc27f04c&")
        embed.set_footer(text="Page 3 of 6 • Use the buttons below to navigate")
        return embed

    def _create_step3_page(self):
        embed = discord.Embed(
            title="Step 3: Click the Ticket Button",
            description="Interact with the ticket bot to start creating your ticket.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🖱️ Action",
            value="Click the button (usually labeled 'Create Ticket' or 'Open Ticket')\n\n"
                  "OR\n\n"
                  "React with the emoji shown on the message",
            inline=False
        )
        embed.add_field(
            name="⏳ What happens next",
            value="The bot will respond and show you a new ticket has been created.",
            inline=False
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1489129854958960751/image.png?ex=69cf4bc0&is=69cdfa40&hm=e7b3a326e24e9f70588184ff007b38b1353daeeac9067698e2100d63d6cdf33e&")
        embed.set_footer(text="Page 4 of 6 • Use the buttons below to navigate")
        return embed

    def _create_step4_page(self):
        embed = discord.Embed(
            title="Step 4: Your Ticket Channel is Created",
            description="A new private channel will be created just for your ticket.",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🎉 Your new channel",
            value="You'll see a new channel appear in your sidebar\n"
                  "Only you and the support team can see it\n"
                  "The bot will send a welcome message",
            inline=False
        )
        embed.add_field(
            name="💬 What to do",
            value="Describe your issue or question clearly in the channel\n"
                  "Include any relevant details",
            inline=False
        )
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1489130486482862151/image.png?ex=69cf4c56&is=69cdfad6&hm=a257829b348f6b70ffb6842a17c7ff480c78e22b03c3c8de067c06c90b37def2&")
        embed.set_footer(text="Page 5 of 6 • Use the buttons below to navigate")
        return embed

    def _create_final_page(self):
        embed = discord.Embed(
            title="Step 5: Wait for Support Team",
            description="✅ You're all set! Your ticket is now open.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📬 What happens now",
            value="A member of the support team will respond to your ticket\n"
                  "They'll help resolve your issue\n"
                  "Keep an eye on the ticket channel for responses",
            inline=False
        )
        embed.add_field(
            name="🕐 Response time",
            value="Support typically responds within a few hours\n"
                  "Stay patient - they're helping as fast as they can!",
            inline=False
        )
        embed.add_field(
            name="❌ Closing your ticket",
            value="Once your issue is resolved, the support team will close the ticket\n"
                  "The channel will be archived for your records",
            inline=False
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/889695047510011974/1489130784257212487/image.png?ex=69cf4c9d&is=69cdfb1d&hm=c57802defd2e4deb3885b17c8d8c4cd8d23d2ae6ae49927c44967c9ad09d4f67&")
        embed.set_footer(text="Page 6 of 6 • Enjoy your ticket! 🎫")
        return embed


class PaginatorView(discord.ui.View):
    def __init__(self, pages, current_page, author_id, timeout=180):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current_page = current_page
        self.author_id = author_id
        
        # Update button states
        self.update_buttons()

    def update_buttons(self):
        """Update button states based on current page"""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="⬅️ Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can't use this button!", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can't use this button!", ephemeral=True)
            return
        
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("You can't use this button!", ephemeral=True)
            return
        
        await interaction.response.defer()
        await interaction.message.delete()
