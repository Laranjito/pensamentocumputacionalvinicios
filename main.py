import random
import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import logging
import os
import asyncio
from dotenv import load_dotenv
import io
from PIL import Image, ImageFont, ImageDraw

load_dotenv()

logging.basicConfig(level=logging.INFO)

bot = commands.Bot(command_prefix="!!", intents=discord.Intents.all(), application_id=int(os.getenv("BOT_ID")))

# Economia
economia = {}

# Sistema de Tickets
tickets = {}
category_id = None  # Variável global para armazenar o ID da categoria de tickets

async def create_ticket_category(guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }
    category = await guild.create_category('Tickets', overwrites=overwrites)
    return category.id

async def get_ticket_category(guild):
    for category in guild.categories:
        if category.name == 'Tickets':
            return category.id
    return await create_ticket_category(guild)

@bot.event
async def on_ready():
    global category_id
    category_id = await get_ticket_category(bot.guilds[0])  # Assume que o bot está em apenas um servidor
    print(f'Ticket category ID: {category_id}')
    print("Estou online!")

@bot.event
async def on_message(message):
    # Verifica se o bot foi mencionado
    if bot.user.mentioned_in(message):
        # Define o prefixo de comando
        command_prefix = "!!"

        # Envia a mensagem com o prefixo de comando
        await message.channel.send(f"Olá {message.author.mention}! Meu prefixo de comando é `{command_prefix}`. Use `{command_prefix}ajuda` para obter mais informações.")

    await bot.process_commands(message)

# Comandos de tickets
@bot.command()
async def ticketopen(ctx):
    """Abre um novo ticket."""
    global category_id

    # Verifica se o autor já tem um ticket aberto
    if ctx.author.id in tickets:
        await ctx.send("Você já tem um ticket aberto.")
        return

    # Cria o canal para o ticket
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }

    ticket_channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.display_name}", category=ctx.guild.get_channel(category_id), overwrites=overwrites)

    # Armazena o ID do canal no dicionário de tickets
    tickets[ctx.author.id] = ticket_channel.id

    # Envia uma mensagem com instruções para fechar o ticket
    await ticket_channel.send(f"Olá {ctx.author.mention}! Este é o seu ticket. Para fechá-lo, use o comando `!!ticketclose`.")

    await ctx.send(f"Ticket aberto! Por favor, vá para {ticket_channel.mention}.")

@bot.command()
async def ticketclose(ctx):
    """Fecha o ticket atual."""
    # Verifica se o autor tem um ticket aberto
    if ctx.author.id not in tickets:
        await ctx.send("Você não tem um ticket aberto.")
        return

    # Obtém o ID do canal do ticket
    ticket_channel_id = tickets.pop(ctx.author.id)

    # Obtém o objeto do canal
    ticket_channel = ctx.guild.get_channel(ticket_channel_id)

    if ticket_channel:
        await ticket_channel.delete()
        await ctx.send("Ticket fechado. Obrigado!")

@bot.command()
async def lock(ctx):
    """Comando para trancar um canal."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("Canal trancado!")

@bot.command()
async def unlock(ctx):
    """Comando para destrancar um canal."""
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("Canal destrancado!")

@bot.command()
async def ship(ctx, user1: discord.User, user2: discord.User):
    porcentagem = random.randint(0, 100)
    nomeship = f"{user1.name[:len(user1.name)//2]}{user2.name[len(user2.name)//2:]}"

    imagem1 = await user1.avatar.read()
    avatar1 = Image.open(io.BytesIO(imagem1))
    avatar1 = avatar1.resize((250, 250))

    imagem2 = await user2.avatar.read()
    avatar2 = Image.open(io.BytesIO(imagem2))
    avatar2 = avatar2.resize((250, 250))

    planodefundo = Image.new("RGB", (500, 280), (56, 56, 56))
    planodefundo.paste(avatar1, (0, 0))
    planodefundo.paste(avatar2, (250, 0))

    fundodraw = ImageDraw.Draw(planodefundo)
    fundodraw.rounded_rectangle(((0, 250), (500 * (porcentagem / 100), 289)), fill=(207, 13, 48), radius=5)

    fonte = ImageFont.truetype("RobotoMono-Bold.ttf", 20)
    fundodraw.text((230, 250), f"{porcentagem}%", font=fonte)

    buffer = io.BytesIO()
    planodefundo.save(buffer, format="PNG")
    buffer.seek(0)

    if porcentagem <= 35:
        mensagem_extra = "😅 Não parece rolar uma química tão grande, mas quem sabe...?"
    elif porcentagem > 35 and porcentagem <= 65:
        mensagem_extra = "☺️ Essa combinação tem potencial, que tal um jantar romântico?"
    elif porcentagem > 65:
        mensagem_extra = "😍 Combinação perfeita! Quando será o casamento?"

    await ctx.send(
        f" **Será que vamos ter um casal novo por aqui?** {user1.mention} + {user2.mention} = ✨ `{nomeship}` ✨\n{mensagem_extra}",
        file=discord.File(fp=buffer, filename="file.png"))

# Comando para limpar mensagens em um canal
@bot.command()
async def clear(ctx, amount: int):
    """Comando para limpar mensagens em um canal."""
    await ctx.channel.purge(limit=amount + 1)  # O +1 é para incluir a mensagem de comando

# Comando para ping
@bot.command()
async def ping(ctx):
    """Comando para verificar a latência do bot."""
    await ctx.send(f'Pong! Latência: {round(bot.latency * 1000)}ms')

# Sistema de Economia
@bot.command()
@cooldown(1, 86400, BucketType.user)  # Um cooldown de 24 horas (86400 segundos)
async def daily(ctx):
    """Recebe uma quantia diária de LaylaCoin."""
    user_id = str(ctx.author.id)
    if user_id not in economia:
        economia[user_id] = 0

    quantia_diaria = random.randint(50, 100)
    economia[user_id] += quantia_diaria

    # Emoji personalizado para LaylaCoin
    layla_coin_emoji = "🪙"

    # Mensagem formatada
    mensagem = f"Você recebeu {quantia_diaria} {layla_coin_emoji} ´´LaylaCoins´´  pela recompensa diária!"

    await ctx.send(mensagem)

@bot.command()
async def saldo(ctx):
    """Verifica o saldo de LaylaCoin."""
    user_id = str(ctx.author.id)
    if user_id not in economia:
        economia[user_id] = 0

    saldo = economia[user_id]
    await ctx.send(f"Seu saldo atual de LaylaCoin é: {saldo} LaylaCoin.")

# Comando de ban
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, motivo='Nenhum motivo fornecido'):
    try:
        await member.ban(reason=motivo)
        await ctx.send(f'{member.mention} foi banido por: {motivo}')
    except discord.Forbidden:
        await ctx.send('Não tenho permissões suficientes para banir esse membro.')

# Comando de unban
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id, *, motivo='Nenhum motivo fornecido'):
    banned_users = await ctx.guild.bans()

    for ban_entry in banned_users:
        if ban_entry.user.id == int(user_id):
            try:
                await ctx.guild.unban(ban_entry.user, reason=motivo)
                await ctx.send(f'{ban_entry.user.mention} foi desbanido por: {motivo}')
                return
            except discord.Forbidden:
                await ctx.send('Não tenho permissões suficientes para desbanir esse membro.')

    await ctx.send('Usuário não encontrado na lista de banidos.')

@bot.command()
async def ajuda(ctx):
    """Mostra informações sobre os comandos disponíveis."""
    embed = discord.Embed(title="Ajuda - Comandos da Layla", color=discord.Color.blue())

    # Comandos de Tickets
    embed.add_field(name="`!!ticketopen`", value="Abre um novo ticket.", inline=False)
    embed.add_field(name="`!!ticketclose`", value="Fecha o ticket atual.", inline=False)

    # Comandos de Controle de Canal
    embed.add_field(name="`!!lock`", value="Tranca o canal.", inline=False)
    embed.add_field(name="`!!unlock`", value="Destranca o canal.", inline=False)

    # Comandos de Entretenimento
    embed.add_field(name="`!!ship`", value="Calcula a afinidade entre dois usuários.", inline=False)

    # Comandos de Limpeza
    embed.add_field(name="`!!clear`", value="Limpa mensagens em um canal.", inline=False)

    # Comandos de Economia
    embed.add_field(name="`!!daily`", value="Recebe uma quantia diária de LaylaCoin.", inline=False)
    embed.add_field(name="`!!saldo`", value="Verifica o saldo de LaylaCoin.", inline=False)
    embed.add_field(name="`!!aposta`", value="Aposta uma quantia de LaylaCoin.", inline=False)
    embed.add_field(name="`!!pagar`", value="Paga uma quantia de LaylaCoin para outro usuário.", inline=False)

    # Comandos de Moderação
    embed.add_field(name="`!!ban`", value="Bane um membro do servidor.", inline=False)
    embed.add_field(name="`!!unban`", value="Desbane um membro do servidor.", inline=False)

    # Comandos de Informações de Usuário
    embed.add_field(name="`!!userinfo`", value="Mostra informações sobre um usuário.", inline=False)

    # Comandos de Utilidade
    embed.add_field(name="`!!suporte`", value="Fornece um link para o servidor de suporte.", inline=False)
    embed.add_field(name="`!!avatar`", value="Mostra o avatar de um usuário.", inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def suporte(ctx):
    """Fornece um link para o servidor de suporte."""
    link = "https://discord.gg/2xRH4CGZ4E"
    mensagem = f"**Clique [aqui]({link}) para ir para o servidor de suporte de Layla.**"
    await ctx.send(mensagem)

@bot.command()
async def avatar(ctx, user: discord.User = None):
    """Mostra o avatar de um usuário."""
    if not user:
        user = ctx.author

    avatar_url = user.avatar_url_as(size=1024)
    await ctx.send(f"Avatar de {user.name}: {avatar_url}")

@bot.command()
async def userinfo(ctx, user: discord.User = None):
    """Mostra informações sobre um usuário."""
    if not user:
        user = ctx.author

    embed = discord.Embed(title="Informações do Usuário", color=0x7289da)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="Nome", value=user.name, inline=True)
    embed.add_field(name="Discriminador", value=user.discriminator, inline=True)
    embed.add_field(name="ID", value=user.id, inline=True)
    embed.add_field(name="Conta Criada em", value=user.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    embed.add_field(name="Entrou no Servidor em", value=user.joined_at.strftime("%d/%m/%Y %H:%M:%S") if user.joined_at else "N/A", inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def userbanner(ctx, user: discord.User = None):
    """Mostra o banner de um usuário."""
    if not user:
        user = ctx.author

    banner_url = user.banner_url_as(format="png", size=1024)
    await ctx.send(f"Banner de {user.name}: {banner_url}")

@bot.command()
async def infoemoji(ctx, emoji: discord.Emoji):
    """Mostra informações sobre um emoji."""
    embed = discord.Embed(title="Informações do Emoji", color=0x7289da)
    embed.set_thumbnail(url=emoji.url)
    embed.add_field(name="Nome", value=emoji.name, inline=True)
    embed.add_field(name="ID", value=emoji.id, inline=True)
    embed.add_field(name="Animação", value="Sim" if emoji.animated else "Não", inline=True)
    embed.add_field(name="Servidor", value=emoji.guild.name, inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def perfil(ctx, user: discord.User = None):
    """Mostra o perfil de um usuário."""
    if not user:
        user = ctx.author

    user_id = str(user.id)

    saldo = economia.get(user_id, 0)
    embed = discord.Embed(title="Perfil de Usuário", color=0x7289da)
    embed.set_thumbnail(url=user.avatar_url)
    embed.add_field(name="Nome", value=user.name, inline=True)
    embed.add_field(name="Saldo de LaylaCoins", value=saldo, inline=True)

    await ctx.send(embed=embed)

@bot.command()
async def pagar(ctx, member: discord.Member, amount: int):
    """Pague LaylaCoins para outro usuário."""
    if amount <= 0:
        await ctx.send("A quantidade deve ser maior que zero.")
        return

    author_id = str(ctx.author.id)
    member_id = str(member.id)

    if author_id not in economia or economia[author_id] < amount:
        await ctx.send("Você não tem LaylaCoins suficientes para fazer isso.")
        return

    economia[author_id] -= amount
    economia[member_id] = economia.get(member_id, 0) + amount

    await ctx.send(f"Você pagou {amount} LaylaCoins para {member.mention}.")

@bot.command()
async def aposta(ctx, amount: int):
    """Aposte LaylaCoins."""
    if amount <= 0:
        await ctx.send("A aposta deve ser maior que zero.")
        return

    author_id = str(ctx.author.id)

    if author_id not in economia or economia[author_id] < amount:
        await ctx.send("Você não tem LaylaCoins suficientes para fazer essa aposta.")
        return

    # Lógica da aposta (você pode personalizar conforme necessário)
    resultado = random.choice([True, False])  # Exemplo: 50% de chance de ganhar
    if resultado:
        economia[author_id] += amount  # Ganhou a aposta
        await ctx.send(f"Parabéns! Você ganhou {amount} LaylaCoins na aposta.")
    else:
        economia[author_id] -= amount  # Perdeu a aposta
        await ctx.send(f"Que pena! Você perdeu {amount} LaylaCoins na aposta.")

async def main():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')

    TOKEN = os.getenv("DISCORD_TOKEN")
    await bot.start(TOKEN)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
