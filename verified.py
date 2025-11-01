import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import json
import os
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

CONFIG_FILE = "server_configs.json"

server_configs = {}


def load_configs():
    global server_configs
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            server_configs = json.load(f)
    else:
        server_configs = {}


def save_configs():
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(server_configs, f, ensure_ascii=False, indent=2)


def get_server_config(guild_id: int):
    guild_id_str = str(guild_id)
    if guild_id_str not in server_configs:
        server_configs[guild_id_str] = {
            "setup_complete": False,
            "embed_title": "이것은 제목(Title)입니다.",
            "embed_description": "이것은 내용입니다. 밑 세팅하기 눌러서 헥스코드(#제외)와 제목과 내용을 입력해주세요",
            "embed_color": "00FF00",
            "button_label": "인증하기",
            "button_emoji": "🔐",
            "verified_role_id": None,
            "log_channel_id": None
        }
        save_configs()
    return server_configs[guild_id_str]


class EmbedSettingModal(discord.ui.Modal, title="임베드 세팅"):
    
    embed_title = discord.ui.TextInput(
        label="임베드 제목",
        placeholder="인증 시스템",
        default="이것은 제목(Title)입니다.",
        max_length=256,
        required=True
    )
    
    embed_description = discord.ui.TextInput(
        label="임베드 내용",
        placeholder="버튼을 눌러 인증하세요",
        style=discord.TextStyle.paragraph,
        default="이것은 내용입니다. 밑 세팅하기 눌러서 헥스코드(#제외)와 제목과 내용을 입력해주세요",
        max_length=4000,
        required=True
    )
    
    embed_color = discord.ui.TextInput(
        label="임베드 색상 (헥스코드, # 제외)",
        placeholder="00FF00",
        default="00FF00",
        min_length=6,
        max_length=6,
        required=True
    )
    
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        config = get_server_config(self.guild_id)
        config["embed_title"] = self.embed_title.value
        config["embed_description"] = self.embed_description.value
        config["embed_color"] = self.embed_color.value
        save_configs()
        
        try:
            embed_color = int(self.embed_color.value, 16)
        except:
            embed_color = 0x00FF00
        
        updated_embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_description.value,
            color=embed_color
        )
        
        view = SetupStep1View(self.guild_id)
        
        await interaction.response.edit_message(embed=updated_embed, view=view)


class ButtonSettingModal(discord.ui.Modal, title="버튼 세팅"):
    
    button_label = discord.ui.TextInput(
        label="버튼 텍스트",
        placeholder="인증하기",
        default="인증하기",
        max_length=80,
        required=True
    )
    
    button_emoji = discord.ui.TextInput(
        label="버튼 이모지 (선택사항)",
        placeholder="🔐",
        default="🔐",
        max_length=2,
        required=False
    )
    
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        config = get_server_config(self.guild_id)
        config["button_label"] = self.button_label.value
        config["button_emoji"] = self.button_emoji.value if self.button_emoji.value else None
        save_configs()
        
        try:
            embed_color = int(config["embed_color"], 16)
        except:
            embed_color = 0x00FF00
        
        updated_embed = discord.Embed(
            title=config["embed_title"],
            description=config["embed_description"],
            color=embed_color
        )
        
        view = SetupStep1View(self.guild_id)
        
        await interaction.response.edit_message(embed=updated_embed, view=view)


class LogChannelModal(discord.ui.Modal, title="로그 채널 설정"):
    
    channel_id = discord.ui.TextInput(
        label="채널 ID",
        placeholder="1234567890123456789",
        min_length=17,
        max_length=20,
        required=True
    )
    
    def __init__(self, guild_id: int):
        super().__init__()
        self.guild_id = guild_id
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.channel_id.value)
            channel = interaction.guild.get_channel(channel_id)
            
            if not channel:
                await interaction.response.send_message(
                    "❌ 해당 ID의 채널을 찾을 수 없습니다. 올바른 채널 ID를 입력해주세요.",
                    ephemeral=True
                )
                return
            
            if not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message(
                    "❌ 텍스트 채널 ID를 입력해주세요.",
                    ephemeral=True
                )
                return
            
            config = get_server_config(self.guild_id)
            config["log_channel_id"] = channel_id
            save_configs()
            
            await interaction.response.send_message(
                f"✅ 로그 채널이 {channel.mention}(으)로 설정되었습니다!",
                ephemeral=True
            )
        except ValueError:
            await interaction.response.send_message(
                "❌ 올바른 채널 ID를 입력해주세요.",
                ephemeral=True
            )


class SetupStartView(discord.ui.View):
    
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
    
    @discord.ui.button(label="시작하기", style=discord.ButtonStyle.green, emoji="✅")
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = SetupStep1View(self.guild_id)
        
        config = get_server_config(self.guild_id)
        try:
            embed_color = int(config["embed_color"], 16)
        except:
            embed_color = 0x00FF00
        
        embed = discord.Embed(
            title=config["embed_title"],
            description=config["embed_description"],
            color=embed_color
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class SetupStep1View(discord.ui.View):
    
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        
        config = get_server_config(guild_id)
        button_label = config.get("button_label", "인증하기")
        button_emoji = config.get("button_emoji", "🔐")
        
        preview_button = discord.ui.Button(
            label=button_label,
            style=discord.ButtonStyle.primary,
            emoji=button_emoji,
            disabled=True,
            row=0
        )
        self.add_item(preview_button)
    
    @discord.ui.button(label="세팅하기", style=discord.ButtonStyle.secondary, row=1)
    async def embed_setting_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = EmbedSettingModal(self.guild_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="버튼 세팅하기", style=discord.ButtonStyle.secondary, row=1)
    async def button_setting_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = ButtonSettingModal(self.guild_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="다음", style=discord.ButtonStyle.green, row=1)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        view = SetupStep2View(self.guild_id, interaction.guild)
        
        embed = discord.Embed(
            title="역할 선택",
            description=(
                "완벽해요 ! 클릭시 지급할 역할을 선택해주세요\n"
                "(봇 역할이 지급될 역할보다 낮다면 지급이 불가능해요 !)"
            ),
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class SetupStep2View(discord.ui.View):
    
    def __init__(self, guild_id: int, guild: discord.Guild):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.add_item(RoleSelectMenu(guild_id, guild))
    
    @discord.ui.button(label="다음", style=discord.ButtonStyle.green)
    async def next_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = get_server_config(self.guild_id)
        
        if not config.get("verified_role_id"):
            await interaction.response.send_message(
                "❌ 먼저 역할을 선택해주세요!",
                ephemeral=True
            )
            return
        
        view = SetupStep3View(self.guild_id)
        
        embed = discord.Embed(
            title="로그 채널 설정",
            description="이제 마지막 !! 로그 채널을 설정해주세요",
            color=discord.Color.blue()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)


class RoleSelectMenu(discord.ui.Select):
    
    def __init__(self, guild_id: int, guild: discord.Guild):
        self.guild_id = guild_id
        
        options = []
        for role in guild.roles:
            if role.name != "@everyone" and not role.managed:
                options.append(
                    discord.SelectOption(
                        label=role.name,
                        value=str(role.id),
                        description=f"ID: {role.id}"
                    )
                )
        
        options = options[:25]
        
        if not options:
            options = [
                discord.SelectOption(
                    label="역할이 없습니다",
                    value="0",
                    description="서버에 역할을 먼저 생성해주세요"
                )
            ]
        
        super().__init__(
            placeholder="역할을 선택하세요...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        
        if not role:
            await interaction.response.send_message(
                "❌ 역할을 찾을 수 없습니다.",
                ephemeral=True
            )
            return
        
        config = get_server_config(self.guild_id)
        config["verified_role_id"] = role_id
        save_configs()
        
        await interaction.response.send_message(
            f"✅ 인증 역할이 {role.mention}(으)로 설정되었습니다!",
            ephemeral=True
        )


class SetupStep3View(discord.ui.View):
    
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
    
    @discord.ui.button(label="로그채널 지정 안하기", style=discord.ButtonStyle.secondary)
    async def no_log_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        config = get_server_config(self.guild_id)
        config["log_channel_id"] = None
        config["setup_complete"] = True
        save_configs()
        
        embed = discord.Embed(
            title="✅ 세팅 완료!",
            description=(
                "세팅이 완료되었어요 ! 이제 `/인증 [해당채널아이디]`를 진행하셔서 인증 시스템을 지금 바로 시작해보세요 !\n\n"
                "💡**Tips**\n"
                "* `/세팅변경` 하시면 임베드와 로그채널 등등 다 변경 가능해요.\n"
                "* 해당 봇은 소스코드를 제공하여 업데이트는 따로 진행하셔야 합니다."
            ),
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="로그채널 지정하기", style=discord.ButtonStyle.primary)
    async def set_log_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        modal = LogChannelModal(self.guild_id)
        await interaction.response.send_modal(modal)
        
        await asyncio.sleep(1)
        
        config = get_server_config(self.guild_id)
        config["setup_complete"] = True
        save_configs()


class VerificationView(discord.ui.View):
    
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        
        config = get_server_config(guild_id)
        button_label = config.get("button_label", "인증하기")
        button_emoji = config.get("button_emoji", "🔐")
        
        self.verify_button = discord.ui.Button(
            label=button_label,
            style=discord.ButtonStyle.success,
            emoji=button_emoji,
            custom_id=f"verify_{guild_id}"
        )
        self.verify_button.callback = self.verify_callback
        self.add_item(self.verify_button)
    
    async def verify_callback(self, interaction: discord.Interaction):
        config = get_server_config(self.guild_id)
        role_id = config.get("verified_role_id")
        
        if not role_id:
            await interaction.response.send_message(
                "❌ 역할이 설정되지 않았습니다. 관리자에게 문의하세요.",
                ephemeral=True
            )
            return
        
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(
                "❌ 역할을 찾을 수 없습니다. 관리자에게 문의하세요.",
                ephemeral=True
            )
            return
        
        if role in interaction.user.roles:
            await interaction.response.send_message(
                "✅ 이미 인증된 사용자입니다!",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        verification_time = random.uniform(1.0, 3.0)
        await asyncio.sleep(verification_time)
        
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        answer = num1 + num2
        
        await asyncio.sleep(0.5)
        
        try:
            await interaction.user.add_roles(role)
            
            await interaction.followup.send(
                f"✅ 인증 완료! {role.name} 역할이 지급되었습니다.\n"
                f"🤖 봇 검증 완료: `{num1} + {num2} = {answer}` ✓",
                ephemeral=True
            )
            
            log_channel_id = config.get("log_channel_id")
            if log_channel_id:
                log_channel = interaction.guild.get_channel(log_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="✅ 인증 로그",
                        description=f"{interaction.user.mention}님이 인증을 완료했습니다.",
                        color=discord.Color.green(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="사용자", value=f"{interaction.user} ({interaction.user.id})")
                    log_embed.add_field(name="역할", value=role.mention)
                    await log_channel.send(embed=log_embed)
        
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ 역할 지급 권한이 없습니다. 봇의 권한을 확인해주세요.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ 오류가 발생했습니다: {str(e)}",
                ephemeral=True
            )


@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 준비되었습니다!')
    print(f'봇 ID: {bot.user.id}')
    print('------')
    
    load_configs()
    
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)}개의 명령어가 동기화되었습니다.')
    except Exception as e:
        print(f'명령어 동기화 중 오류 발생: {e}')


@bot.tree.command(name="서버세팅", description="인증 봇 초기 세팅을 시작합니다")
@app_commands.default_permissions(administrator=True)
async def server_setup(interaction: discord.Interaction):
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
            ephemeral=True
        )
        return
    
    config = get_server_config(interaction.guild_id)
    
    if config["setup_complete"]:
        await interaction.response.send_message(
            "✅ 이미 세팅이 완료되었습니다! `/세팅변경` 명령어로 설정을 변경하세요.",
            ephemeral=True
        )
        return
    
    embed = discord.Embed(
        title="반갑습니다 !",
        description=(
            "**Nuvex 소스코드**를 이용해주셔서 대단히 감사합니다.\n"
            "밑 버튼을 눌러 해당 '인증 봇' 세팅을 진행해주세요.\n"
            "나중에 `/세팅변경` 으로 바꾸실 수 있습니다 !\n\n"
            "(SQL 인젝션 방지로 json으로 저장합니다.)"
        ),
        color=discord.Color.blue()
    )
    
    view = SetupStartView(interaction.guild_id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="세팅변경", description="인증 봇 설정을 변경합니다")
@app_commands.default_permissions(administrator=True)
async def change_settings(interaction: discord.Interaction):
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
            ephemeral=True
        )
        return
    
    config = get_server_config(interaction.guild_id)
    
    if not config["setup_complete"]:
        await interaction.response.send_message(
            "❌ 먼저 `/서버세팅` 명령어로 초기 세팅을 완료해주세요!",
            ephemeral=True
        )
        return
    
    # 1단계 View로 이동
    view = SetupStep1View(interaction.guild_id)
    
    try:
        embed_color = int(config["embed_color"], 16)
    except:
        embed_color = 0x00FF00
    
    embed = discord.Embed(
        title=config["embed_title"],
        description=config["embed_description"],
        color=embed_color
    )
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="인증", description="인증 시스템을 지정한 채널에 생성합니다")
@app_commands.describe(채널="인증 버튼을 생성할 채널")
@app_commands.default_permissions(administrator=True)
async def setup_verification(
    interaction: discord.Interaction,
    채널: discord.TextChannel
):
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
            ephemeral=True
        )
        return
    
    config = get_server_config(interaction.guild_id)
    
    if not config["setup_complete"]:
        await interaction.response.send_message(
            "❌ 먼저 `/서버세팅` 명령어로 초기 세팅을 완료해주세요!",
            ephemeral=True
        )
        return
    
    if not config.get("verified_role_id"):
        await interaction.response.send_message(
            "❌ 역할이 설정되지 않았습니다. `/세팅변경`으로 역할을 설정해주세요.",
            ephemeral=True
        )
        return
    
    # 임베드 생성
    try:
        embed_color = int(config["embed_color"], 16)
    except:
        embed_color = 0x00FF00
    
    embed = discord.Embed(
        title=config["embed_title"],
        description=config["embed_description"],
        color=embed_color
    )
    
    # View 생성
    view = VerificationView(interaction.guild_id)
    
    # 채널에 메시지 전송
    try:
        await 채널.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ {채널.mention} 채널에 인증 시스템이 생성되었습니다!",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ {채널.mention} 채널에 메시지를 보낼 권한이 없습니다.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ 오류가 발생했습니다: {str(e)}",
            ephemeral=True
        )


if __name__ == "__main__":
    TOKEN = "YOUT_BOT_TOKEN_HERE"
    
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ 오류: 봇 토큰을 설정해주세요!")
        print("TOKEN 변수에 실제 봇 토큰을 입력하세요.")
    else:
        bot.run(TOKEN)
