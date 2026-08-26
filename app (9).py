# ==========================================================================
#  DERP SERVICES - DISCORD BOT  (single file)
# ==========================================================================
#
#  #########################################################################
#  ##                                                                     ##
#  ##                   SECTION 1  -  SETTINGS                            ##
#  ##          THIS IS THE ONLY PART YOU EVER NEED TO EDIT                ##
#  ##                                                                     ##
#  #########################################################################

import os
import io
import asyncio
import json
import datetime

import discord
from discord import app_commands
from discord.ext import commands

# ---- BOT LOGIN -----------------------------------------------------------
DISCORD_TOKEN = "MTUzNTAzMTU2MzkyOTEyOTA5Mw.Gv9NhK.b3p65HOC-XyO4NfdD2pvTQaWHVYohpicBvVLLE"
CLIENT_ID = "1535031563929129093"          # application (client) id
OWNER_ID  = "1373295966551146569"          # your personal discord id
GUILD_ID  = "1542231203367755826"          # your server id

CONFIG = {
    # ---- BRANDING --------------------------------------------------------
    "shopName": "DERP Services",
    "brandColor": 0x9B59B6,
    "logoURL": "",
    "footerText": "Trusted Blox Fruits Trader",

    # ---- CHANNELS & CATEGORIES (IDs) -------------------------------------
    "ticketCategoryId": 1542265854480224326,   # buy/sell/service tickets go here
    "staffAppCategoryId": 1542265854480224326, # staff applications go here (can be same)
    "vouchChannelId": 1542265589874032711,     # vouches get posted here
    "logChannelId": 1542265614050140311,       # ticket logs + transcripts go here

    # ---- ROLES -----------------------------------------------------------
    "staffRoleId": 1542266212451614800,        # pinged in tickets + can claim/close/verify

    # ---- TICKET TYPES (shown in the dropdown) ----------------------------
    "ticketTypes": [
        {"id": "buy",     "label": "Buy",               "emoji": "🛒", "description": "Buy a fruit / item from us"},
        {"id": "sell",    "label": "Sell",              "emoji": "💰", "description": "Sell your fruit / item to us"},
        {"id": "service", "label": "Service",           "emoji": "🛠️", "description": "Order a service (level, raid, etc.)"},
        {"id": "staff",   "label": "Staff Application",  "emoji": "📋", "description": "Apply to join our staff team"},
    ],
    "maxOpenTicketsPerUser": 2,
    "sendTranscriptToUserDM": True,

    # ---- PAYMENT METHODS (put your real wallet/UPI here) -----------------
    "paymentInfo": {
        "LTC":  "ltc1qvvrhug3qg8w5gcvue54mtnpmzywnwagusxl4ah",
        "INR":  "UPI: 9431534468@fam",
    },

    # ---- STOCK & PRICES --------------------------------------------------
    "fruits": [
        {"name": "Kitsune", "emoji": "🦊", "price": "$25 / 10,000 Robux", "stock": 2},
        {"name": "Leopard", "emoji": "🐆", "price": "$12 / 4,500 Robux",  "stock": 5},
        {"name": "Dragon",  "emoji": "🐉", "price": "$10 / 4,000 Robux",  "stock": 3},
        {"name": "Dough",   "emoji": "🍩", "price": "$6 / 2,400 Robux",   "stock": 8},
        {"name": "Venom",   "emoji": "🐍", "price": "$5 / 2,000 Robux",   "stock": 6},
        {"name": "Buddha",  "emoji": "🧘", "price": "$4 / 1,600 Robux",   "stock": 10},
        {"name": "Spirit",  "emoji": "👻", "price": "$8 / 3,200 Robux",   "stock": 0},
        {"name": "Shadow",  "emoji": "🌑", "price": "$7 / 2,800 Robux",   "stock": 4},
        {"name": "Control", "emoji": "🎮", "price": "$5 / 2,000 Robux",   "stock": 3},
        {"name": "Gravity", "emoji": "🌌", "price": "$3 / 1,200 Robux",   "stock": 7},
    ],
}


#  #########################################################################
#  ##                                                                     ##
#  ##                   SECTION 2  -  MAIN CODE                           ##
#  ##            DO NOT EDIT ANYTHING BELOW THIS LINE                     ##
#  ##                                                                     ##
#  #########################################################################

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", DISCORD_TOKEN)
GUILD_ID = os.getenv("GUILD_ID", GUILD_ID)
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

PAYMENT_TYPES = {"buy", "sell", "service"}


# ---- Storage -------------------------------------------------------------
def _load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Could not read data.json, starting fresh: {e}")
    seed = {"stock": {}, "vouches": []}
    for fruit in CONFIG["fruits"]:
        seed["stock"][fruit["name"].lower()] = fruit["stock"]
    _save(seed)
    return seed


def _save(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_fruits():
    data = _load()
    result = []
    for fruit in CONFIG["fruits"]:
        merged = dict(fruit)
        merged["stock"] = data["stock"].get(fruit["name"].lower(), fruit["stock"])
        result.append(merged)
    return result


def set_stock(fruit_name, amount):
    data = _load()
    data["stock"][fruit_name.lower()] = max(0, amount)
    _save(data)
    return data["stock"][fruit_name.lower()]


def add_vouch(vouch):
    data = _load()
    data["vouches"].append(vouch)
    _save(data)
    return len(data["vouches"])


def get_vouches():
    return _load()["vouches"]


# ---- Bot setup -----------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def base_embed():
    e = discord.Embed(color=CONFIG["brandColor"])
    e.set_footer(text=CONFIG["footerText"])
    if CONFIG.get("logoURL"):
        e.set_thumbnail(url=CONFIG["logoURL"])
    return e


def is_staff(member: discord.Member) -> bool:
    if member is None:
        return False
    if getattr(member, "guild_permissions", None) and member.guild_permissions.manage_guild:
        return True
    return any(r.id == CONFIG["staffRoleId"] for r in getattr(member, "roles", []))


def stock_embed():
    lines = []
    for f in get_fruits():
        badge = f"`{f['stock']} in stock`" if f["stock"] > 0 else "`❌ OUT OF STOCK`"
        lines.append(f"{f['emoji']} **{f['name']}** — {f['price']}  •  {badge}")
    e = base_embed()
    e.title = f"🏷️ {CONFIG['shopName']} — Stock & Prices"
    e.description = "\n".join(lines)
    e.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return e


def parse_ticket_topic(topic):
    if not topic or not topic.startswith("ticket|"):
        return None
    parts = topic.split("|")
    return {"userId": int(parts[1]), "type": parts[2] if len(parts) > 2 else "buy"}


def payment_info_text():
    lines = []
    for k, v in CONFIG.get("paymentInfo", {}).items():
        lines.append(f"**{k}:** {v}")
    return "\n".join(lines) if lines else "Ask staff for payment details."


async def build_transcript(channel: discord.TextChannel) -> str:
    msgs = [m async for m in channel.history(limit=1000, oldest_first=True)]
    lines = []
    for m in msgs:
        time = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
        content = m.content or ""
        if m.embeds:
            emb = m.embeds[0]
            content += f" [embed: {emb.title or emb.description or 'embed'}]"
        if m.attachments:
            content += " " + " ".join(a.url for a in m.attachments)
        lines.append(f"[{time}] {m.author}: {content}")
    header = (
        f"Transcript for #{channel.name}\n"
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
        f"Total messages: {len(msgs)}\n" + "=" * 50 + "\n"
    )
    return header + "\n".join(lines)


# ---- Modals (the pop-up question forms) ----------------------------------
class BuyModal(discord.ui.Modal, title="Buy Request"):
    item = discord.ui.TextInput(label="What do you want to buy?",
                                style=discord.TextStyle.paragraph, required=True, max_length=500)
    payment = discord.ui.TextInput(label="Payment method (LTC / USDT / INR)",
                                   required=True, max_length=50)
    budget = discord.ui.TextInput(label="Your budget / offer", required=False, max_length=100)
    invited = discord.ui.TextInput(label="Who invited you? (optional)", required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "buy", [
            ("🛒 Wants to buy", str(self.item)),
            ("💳 Payment method", str(self.payment)),
            ("💰 Budget / offer", str(self.budget)),
            ("👥 Invited by", str(self.invited)),
        ])


class SellModal(discord.ui.Modal, title="Sell Request"):
    item = discord.ui.TextInput(label="What do you want to sell?",
                                style=discord.TextStyle.paragraph, required=True, max_length=500)
    price = discord.ui.TextInput(label="Your asking price", required=True, max_length=100)
    payment = discord.ui.TextInput(label="How you want to be paid (LTC/USDT/INR)",
                                   required=True, max_length=50)
    invited = discord.ui.TextInput(label="Who invited you? (optional)", required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "sell", [
            ("💰 Wants to sell", str(self.item)),
            ("🏷️ Asking price", str(self.price)),
            ("💳 Wants payment via", str(self.payment)),
            ("👥 Invited by", str(self.invited)),
        ])


class ServiceModal(discord.ui.Modal, title="Service Request"):
    service = discord.ui.TextInput(label="Which service do you want?",
                                   style=discord.TextStyle.paragraph, required=True, max_length=500)
    payment = discord.ui.TextInput(label="Payment method (LTC / USDT / INR)",
                                   required=True, max_length=50)
    invited = discord.ui.TextInput(label="Who invited you?", required=True, max_length=100)
    piloting = discord.ui.TextInput(label="Account piloting? (yes / no)", required=True, max_length=10)
    notes = discord.ui.TextInput(label="Anything else? (optional)",
                                 style=discord.TextStyle.paragraph, required=False, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "service", [
            ("🛠️ Service wanted", str(self.service)),
            ("💳 Payment method", str(self.payment)),
            ("👥 Invited by", str(self.invited)),
            ("🎮 Account piloting", str(self.piloting)),
            ("📝 Notes", str(self.notes)),
        ])


class StaffAppModal(discord.ui.Modal, title="Staff Application"):
    role = discord.ui.TextInput(label="Which role? (Marketing/Helper/Support)", required=True, max_length=60)
    hours = discord.ui.TextInput(label="How many hours/day can you provide?", required=True, max_length=60)
    location = discord.ui.TextInput(label="Where are you from? (country+timezone)", required=True, max_length=100)
    age = discord.ui.TextInput(label="Your age", required=False, max_length=10)
    experience = discord.ui.TextInput(label="Your experience (optional)",
                                      style=discord.TextStyle.paragraph, required=False, max_length=700)

    async def on_submit(self, interaction: discord.Interaction):
        await create_ticket(interaction, "staff", [
            ("💼 Applying for", str(self.role)),
            ("⏰ Hours per day", str(self.hours)),
            ("🌍 From (country/timezone)", str(self.location)),
            ("🎂 Age", str(self.age)),
            ("📜 Experience", str(self.experience)),
        ])


MODALS = {"buy": BuyModal, "sell": SellModal, "service": ServiceModal, "staff": StaffAppModal}


# ---- Views (buttons & dropdown) ------------------------------------------
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label=t["label"], value=t["id"],
                                 description=t["description"], emoji=t["emoji"])
            for t in CONFIG["ticketTypes"]
        ]
        self.add_item(TicketSelect(options))


class TicketSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(custom_id="ticket_select",
                         placeholder="🎫 Open a ticket — choose a reason...",
                         options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        type_id = self.values[0]
        modal_cls = MODALS.get(type_id)
        if modal_cls:
            await interaction.response.send_modal(modal_cls())
        else:
            await interaction.response.send_message("❌ Unknown ticket type.", ephemeral=True)


class PaymentControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", emoji="✋", style=discord.ButtonStyle.primary, custom_id="claim_ticket")
    async def claim(self, interaction, button):
        await claim_ticket(interaction)

    @discord.ui.button(label="Payment Sent", emoji="✅", style=discord.ButtonStyle.success, custom_id="pay_sent")
    async def pay_sent(self, interaction, button):
        await payment_sent(interaction)

    @discord.ui.button(label="Payment Received", emoji="💰", style=discord.ButtonStyle.secondary, custom_id="pay_received")
    async def pay_received(self, interaction, button):
        await payment_received(interaction)

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction, button):
        await ask_close_confirm(interaction)


class BasicControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Claim", emoji="✋", style=discord.ButtonStyle.primary, custom_id="claim_ticket_b")
    async def claim(self, interaction, button):
        await claim_ticket(interaction)

    @discord.ui.button(label="Close", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_b")
    async def close(self, interaction, button):
        await ask_close_confirm(interaction)


class CloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Yes, close it", emoji="🔒", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction, button):
        await close_ticket(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction, button):
        await interaction.response.edit_message(content="❎ Close cancelled.", view=None)


# ---- Ticket actions ------------------------------------------------------
async def create_ticket(interaction: discord.Interaction, type_id: str, answers):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    ttype = next((t for t in CONFIG["ticketTypes"] if t["id"] == type_id), CONFIG["ticketTypes"][0])

    open_for_user = [
        c for c in guild.text_channels
        if (t := parse_ticket_topic(c.topic)) and t["userId"] == interaction.user.id
    ]
    if len(open_for_user) >= CONFIG.get("maxOpenTicketsPerUser", 2):
        await interaction.followup.send(
            f"❌ You already have {len(open_for_user)} open ticket(s). Please use those first.",
            ephemeral=True,
        )
        return

    staff_role = guild.get_role(CONFIG["staffRoleId"])
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, attach_files=True
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True, manage_channels=True
        ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True, read_message_history=True
        )

    cat_id = CONFIG["staffAppCategoryId"] if type_id == "staff" else CONFIG["ticketCategoryId"]
    category = guild.get_channel(cat_id)
    prefix = "apply" if type_id == "staff" else type_id
    channel = await guild.create_text_channel(
        name=f"{prefix}-{interaction.user.name}"[:90],
        category=category if isinstance(category, discord.CategoryChannel) else None,
        topic=f"ticket|{interaction.user.id}|{type_id}",
        overwrites=overwrites,
    )

    e = base_embed()
    e.title = f"{ttype['emoji']} {ttype['label']} Ticket"
    e.description = f"Opened by {interaction.user.mention}"
    for name, value in answers:
        v = (value or "").strip()
        if v:
            e.add_field(name=name, value=v[:1024], inline=False)
    e.add_field(name="Status", value="🟡 Unclaimed — waiting for staff", inline=False)
    e.timestamp = datetime.datetime.now(datetime.timezone.utc)

    if type_id in PAYMENT_TYPES:
        view = PaymentControlView()
    else:
        view = BasicControlView()

    ping = staff_role.mention if staff_role else ""
    await channel.send(content=f"{ping} {interaction.user.mention}".strip(), embed=e, view=view)

    if type_id in PAYMENT_TYPES:
        pe = base_embed()
        pe.title = "💳 Payment Instructions"
        pe.description = (
            f"{payment_info_text()}\n\n"
            "**How it works:**\n"
            "1️⃣ Client sends the agreed payment.\n"
            "2️⃣ Client clicks **✅ Payment Sent**.\n"
            "3️⃣ Staff verifies and clicks **💰 Payment Received**.\n\n"
            "⚠️ Always wait for staff to confirm before trading."
        )
        await channel.send(embed=pe)

    log_ch = guild.get_channel(CONFIG["logChannelId"])
    if log_ch:
        le = base_embed()
        le.description = f"🎫 **{ttype['label']}** ticket opened by {interaction.user.mention} → {channel.mention}"
        try:
            await log_ch.send(embed=le)
        except Exception:
            pass

    await interaction.followup.send(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)


async def claim_ticket(interaction: discord.Interaction):
    ticket = parse_ticket_topic(interaction.channel.topic if interaction.channel else None)
    if not ticket:
        await interaction.response.send_message("❌ This isn't a ticket channel.", ephemeral=True)
        return
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Only staff can claim tickets.", ephemeral=True)
        return

    msg = interaction.message
    new_embed = discord.Embed.from_dict(msg.embeds[0].to_dict())
    fields = new_embed.to_dict().get("fields", [])
    new_embed.clear_fields()
    for f in fields:
        if f["name"] == "Status":
            new_embed.add_field(name="Status", value=f"🟢 Claimed by {interaction.user.mention}", inline=False)
        else:
            new_embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))
    await msg.edit(embed=new_embed)
    await interaction.response.send_message(
        f"✋ {interaction.user.mention} has claimed this ticket and will help you now."
    )


async def payment_sent(interaction: discord.Interaction):
    ticket = parse_ticket_topic(interaction.channel.topic if interaction.channel else None)
    if not ticket:
        await interaction.response.send_message("❌ This isn't a ticket channel.", ephemeral=True)
        return
    staff_role = interaction.guild.get_role(CONFIG["staffRoleId"])
    ping = staff_role.mention if staff_role else "Staff"
    e = base_embed()
    e.title = "✅ Payment Marked as Sent"
    e.description = (
        f"{interaction.user.mention} has marked the payment as **SENT**.\n"
        f"{ping} please verify and click **💰 Payment Received**."
    )
    await interaction.response.send_message(content=ping, embed=e)


async def payment_received(interaction: discord.Interaction):
    ticket = parse_ticket_topic(interaction.channel.topic if interaction.channel else None)
    if not ticket:
        await interaction.response.send_message("❌ This isn't a ticket channel.", ephemeral=True)
        return
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Only staff can confirm payment.", ephemeral=True)
        return
    e = base_embed()
    e.title = "💰 Payment Confirmed"
    e.description = f"Payment has been **verified & received** by {interaction.user.mention}. ✅\nYou may proceed with the deal."
    await interaction.response.send_message(embed=e)


async def ask_close_confirm(interaction: discord.Interaction):
    ticket = parse_ticket_topic(interaction.channel.topic if interaction.channel else None)
    if not ticket:
        await interaction.response.send_message("❌ This isn't a ticket channel.", ephemeral=True)
        return
    await interaction.response.send_message(
        "⚠️ Are you sure you want to close this ticket? A transcript will be saved.",
        view=CloseConfirmView(), ephemeral=True,
    )


async def close_ticket(interaction: discord.Interaction):
    channel = interaction.channel
    ticket = parse_ticket_topic(channel.topic if channel else None)
    if not ticket:
        await interaction.response.send_message(
            "❌ This command only works inside a ticket channel.", ephemeral=True)
        return
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Only staff can close tickets.", ephemeral=True)
        return

    if interaction.response.is_done():
        await interaction.followup.send("🔒 Closing ticket & saving transcript...")
    else:
        await interaction.response.send_message("🔒 Closing ticket & saving transcript...")

    try:
        transcript = await build_transcript(channel)
    except Exception as ex:
        transcript = f"Transcript unavailable: {ex}"
    fname = f"transcript-{channel.name}.txt"

    log_ch = interaction.guild.get_channel(CONFIG["logChannelId"])
    if log_ch:
        e = base_embed()
        e.description = (
            f"🔒 Ticket **{channel.name}** closed by {interaction.user.mention}\n"
            f"👤 Opened by <@{ticket['userId']}>"
        )
        try:
            await log_ch.send(embed=e, file=discord.File(io.BytesIO(transcript.encode("utf-8")), filename=fname))
        except Exception:
            pass

    if CONFIG.get("sendTranscriptToUserDM"):
        try:
            owner = await bot.fetch_user(ticket["userId"])
            await owner.send(
                content=(f"Here's a copy of your ticket transcript from **{CONFIG['shopName']}**. "
                         f"Thanks! ⭐ Consider leaving a `/vouch`."),
                file=discord.File(io.BytesIO(transcript.encode("utf-8")), filename=fname),
            )
        except Exception:
            pass

    await asyncio.sleep(5)
    try:
        await channel.delete()
    except Exception:
        pass


# ---- Slash commands ------------------------------------------------------
@bot.tree.command(name="panel", description="Post the ticket panel (staff only)")
async def panel(interaction: discord.Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        return
    e = base_embed()
    e.title = f"🎫 {CONFIG['shopName']}"
    e.description = "\n".join([
        "Welcome! Select an option below to open a private ticket.",
        "",
        "🛒 **Buy** — buy a fruit/item from us",
        "💰 **Sell** — sell your fruit/item to us",
        "🛠️ **Service** — order a service (leveling, raids, etc.)",
        "📋 **Staff Application** — apply to join the team",
        "",
        "📦 Use `/stock` to see live stock & prices.",
        "⭐ Use `/vouch` after your deal to leave a review!",
    ])
    await interaction.channel.send(embed=e, view=TicketPanelView())
    await interaction.response.send_message("✅ Panel posted.", ephemeral=True)


@bot.tree.command(name="stock", description="Show the current fruit stock and prices")
async def stock_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=stock_embed())


@bot.tree.command(name="price", description="Check the price of a specific fruit")
@app_commands.describe(fruit="Fruit name (e.g. Dragon)")
async def price_cmd(interaction: discord.Interaction, fruit: str):
    match = next((f for f in get_fruits() if f["name"].lower() == fruit.lower()), None)
    if not match:
        await interaction.response.send_message(
            f"❌ No fruit named **{fruit}** found. Use `/stock` to see the list.", ephemeral=True)
        return
    e = base_embed()
    e.title = f"{match['emoji']} {match['name']}"
    e.add_field(name="Price", value=match["price"], inline=True)
    e.add_field(name="Stock",
                value=f"{match['stock']} available" if match["stock"] > 0 else "Out of stock",
                inline=True)
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="setstock", description="Set the stock count for a fruit (staff only)")
@app_commands.describe(fruit="Fruit name", amount="New stock count")
async def setstock_cmd(interaction: discord.Interaction, fruit: str, amount: int):
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Staff only.", ephemeral=True)
        return
    match = next((f for f in get_fruits() if f["name"].lower() == fruit.lower()), None)
    if not match:
        await interaction.response.send_message(f"❌ No fruit named **{fruit}** in the config.", ephemeral=True)
        return
    new_stock = set_stock(match["name"], max(0, amount))
    await interaction.response.send_message(f"✅ **{match['name']}** stock set to **{new_stock}**.")


@bot.tree.command(name="vouch", description="Leave a vouch/review after a completed deal")
@app_commands.describe(stars="Rating from 1 to 5", comment="What did you buy / how was it?")
async def vouch_cmd(interaction: discord.Interaction, stars: app_commands.Range[int, 1, 5], comment: str):
    total = add_vouch({
        "userId": interaction.user.id, "tag": str(interaction.user),
        "stars": stars, "comment": comment,
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    e = base_embed()
    e.title = "⭐ New Vouch!"
    e.description = f"{'⭐' * stars}{'▫️' * (5 - stars)}\n\n> {comment}"
    e.add_field(name="From", value=interaction.user.mention, inline=True)
    e.set_thumbnail(url=interaction.user.display_avatar.url)
    e.timestamp = datetime.datetime.now(datetime.timezone.utc)
    vouch_ch = interaction.guild.get_channel(CONFIG["vouchChannelId"])
    if vouch_ch:
        try:
            await vouch_ch.send(embed=e)
        except Exception:
            pass
    await interaction.response.send_message(f"✅ Thanks for your vouch! You're vouch #{total}.", ephemeral=True)


@bot.tree.command(name="vouches", description="Show total vouches and average rating")
async def vouches_cmd(interaction: discord.Interaction):
    vouches = get_vouches()
    if not vouches:
        await interaction.response.send_message("No vouches yet — be the first! Use `/vouch`.")
        return
    avg = sum(v["stars"] for v in vouches) / len(vouches)
    e = base_embed()
    e.title = f"⭐ {CONFIG['shopName']} — Reputation"
    e.add_field(name="Total Vouches", value=str(len(vouches)), inline=True)
    e.add_field(name="Average Rating", value=f"{avg:.2f} / 5", inline=True)
    await interaction.response.send_message(embed=e)


@bot.tree.command(name="close", description="Close the current ticket (staff only)")
async def close_cmd(interaction: discord.Interaction):
    await close_ticket(interaction)


# ---- Startup -------------------------------------------------------------
@bot.event
async def on_ready():
    bot.add_view(TicketPanelView())
    bot.add_view(PaymentControlView())
    bot.add_view(BasicControlView())
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as ex:
        print(f"⚠️ Command sync failed: {ex}")
    print(f"✅ Logged in as {bot.user}")


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ No DISCORD_TOKEN set. Edit the DISCORD_TOKEN line in Section 1.")
        raise SystemExit(1)
    bot.run(DISCORD_TOKEN)
