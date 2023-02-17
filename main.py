import nextcord
import requests
import json
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from api import Rank, Normal, ARAM
# 봇 토큰
TOKEN = "ODEwMDc3MzMwNTYzMjY4NjY4.GfDwMD.1G7DURjZKZsxfWt_5rmNezsjN4ghpxLoc-gZ7M"

# Riot API 키
API_KEY = "RGAPI-26e79374-832e-4716-a459-ec9d1149f23a"

intents = nextcord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)

region = 'kr'

# Function to get summoner icon URL
def get_icon(summoner_id):
    icon_url = f'https://kr.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={API_KEY}'
    response = requests.get(icon_url)
    print(icon_url)
    # Check the response code
    if response.status_code != 200:
        print('Error:', response.status_code)
        return None
    data = json.loads(response.text)
    icon_id = data['profileIconId']
    icon_url = f'http://ddragon.leagueoflegends.com/cdn/13.3.1/img/profileicon/{icon_id}.png'
    print(icon_url)
    return icon_url

# Function to get summoner rank data
def get_rank(summoner_id):
    rank_url = f'https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={API_KEY}'
    response = requests.get(rank_url)
    data = json.loads(response.text)
    rank_data = {}
    for entry in data:
        if entry['queueType'] == 'RANKED_SOLO_5x5':
            rank_data['tier'] = entry['tier']
            rank_data['rank'] = entry['rank']
            rank_data['lp'] = entry['leaguePoints']
            rank_data['win'] = entry['wins']
            rank_data['loss'] = entry['losses']
    return rank_data

def game_mode_data(mode_data):
    game_mode = {}
    if mode_data == 400:
        game_mode = '일반'
    elif mode_data == 420:
        game_mode = '솔로 랭크'
    elif mode_data == 430:
        game_mode = '일반'
    elif mode_data == 440:
        game_mode = '자유 랭크'
    elif mode_data == 450:
        game_mode = '무작위 총력전'
    elif mode_data == 700:
        game_mode = '격전'
    elif mode_data == 800:
        game_mode = 'AI 대전'
    elif mode_data == 810:
        game_mode = 'AI 대전'
    elif mode_data == 820:
        game_mode = 'AI 대전'
    elif mode_data == 830:
        game_mode = 'AI 대전'
    elif mode_data == 840:
        game_mode = 'AI 대전'
    elif mode_data == 850:
        game_mode = 'AI 대전'
    elif mode_data == 900:
        game_mode = 'U.R.F'
    elif mode_data == 920:
        game_mode = '포로왕'
    elif mode_data == 1020:
        game_mode = '단일'
    elif mode_data == 1300:
        game_mode = '돌격! 넥서스'
    elif mode_data == 1400:
        game_mode = '궁극기 주문서'
    elif mode_data == 2000:
        game_mode = '튜토리얼'
    elif mode_data == 2010:
        game_mode = '튜토리얼'
    elif mode_data == 2020:
        game_mode = '튜토리얼'
    return game_mode

def game_map_data(map_data):
    game_map = {}
    if map_data == 1:
        game_map = '소환사의 협곡'
    elif map_data == 2:
        game_map = '소환사의 협곡'
    elif map_data == 3:
        game_map = '튜토리얼 맵'
    elif map_data == 4:
        game_map = '뒤틀린 숲'
    elif map_data == 8:
        game_map = '수정의 상처'
    elif map_data == 10:
        game_map = '뒤틀린 숲'
    elif map_data == 11:
        game_map = '소환사의 협곡'
    elif map_data == 12:
        game_map = '칼바람 나락'
    elif map_data == 14:
        game_map = '도살자의 다리'
    elif map_data == 16:
        game_map = '우주 유적'
    elif map_data == 18:
        game_map = '발로란 도시 공원'
    elif map_data == 19:
        game_map = 'Substructure 43'
    elif map_data == 20:
        game_map = 'Crash Site'
    elif map_data == 21:
        game_map = 'Nexus Blitz'
    elif map_data == 22:
        game_map = 'Convergence'
    return game_map

# Function to get recent match history
def get_recent_matches(puuid, region):
    matches_url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5&api_key={API_KEY}'
    response = requests.get(matches_url)
    match_ids = json.loads(response.text)
    matches = []
    for match_id in match_ids:
        match_url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={API_KEY}'
        print(match_url)
        response = requests.get(match_url)
        match_data = json.loads(response.text)
        if 'info' not in match_data:
            continue
        for participant in match_data['info']['participants']:
            if participant['puuid'] == puuid:
                champion_id = participant['championId']
                champion_name = get_champion_name(champion_id)
                print(match_data['info']['queueId'])
                mode_data = match_data['info']['queueId']
                game_mode = game_mode_data(mode_data)
                print(game_mode)
                match = {}
                match['gamemode'] = game_mode
                match['champion_name'] = champion_name
                match['win'] = participant['win']
                match['kda'] = f"{participant['kills']}/{participant['deaths']}/{participant['assists']}"
                matches.append(match)
                break
    return matches



def get_champion_name(champion_id):
    champion_url = f'http://ddragon.leagueoflegends.com/cdn/13.3.1/data/ko_KR/champion.json'
    response = requests.get(champion_url)
    data = json.loads(response.text)
    champions = data['data']
    for champion in champions.values():
        if int(champion['key']) == champion_id:
            return champion['name']
    return 'Unknown'

# Event to handle incoming messages
@client.slash_command(name='rank', description='소환사의 전적을 검색합니다.')
async def search_rank(ctx, summoner_name: str = SlashOption(description='소환사 이름을 입력해주세요.')):
   
    # Check if the message is a command and from an authorized user
    if ctx.user == client.user:
        return
    
    response_msg = await ctx.send(f'```css\n약 5초 정도 소요됩니다.```')  

    try:
        if len(summoner_name) == 2:
            summoner_name = summoner_name[0] + ' ' + summoner_name[1]
        else:
            summoner_name = summoner_name
    except TypeError:
         await response_msg.edit(f'```css\nsummoner_name을 선택하고 소환사 이름을 입력해주세요.```')
         return
        
    region = 'kr'
    summoner_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={API_KEY}'
    print(summoner_url)
    response = requests.get(summoner_url)
    print(summoner_name)
    print(response.status_code)
    if response.status_code != 200:
        await response_msg.edit(f'```css\n소환사를 찾을 수 없습니다.```')
        return
    data = json.loads(response.text)
    summoner__name = data['name']
    print(summoner__name)
    summoner_id = data['id']
    puuid = data['puuid']
    print(f"ID:{summoner_id}")
    icon_url = get_icon(summoner_id)
    rank_data = get_rank(summoner_id)
    '''
    if not rank_data:
        await message.channel.send('')
        return'''
    try:
        tier = rank_data['tier']
    except KeyError:
        tier = '언랭'
    try:
        rank = rank_data['rank']
    except KeyError:
        rank = ' '
    try:
        lp = rank_data['lp']
    except KeyError:
        lp = ' '
    try:
        win = rank_data['win']
    except KeyError:
        win = '언랭'
    try:
        loss = rank_data['loss']
    except KeyError:
        loss = ' '

    recent_matches = get_recent_matches(puuid, 'asia')
    # Create and send embed message
    re_name = summoner_name.strip().replace(' ', '%20')
    opggurl= f'https://www.op.gg/summoners/kr/{re_name}/'
    print(opggurl)
    embed = nextcord.Embed(title=summoner__name, color=nextcord.Color.blue(), url=opggurl)
    embed.set_thumbnail(url=icon_url)
    if lp == ' ':
        lp = ' '
    else:
        lp = f'({lp} LP)'
    embed.add_field(name='랭크', value=f'{tier} {rank} {lp}')
    if win == '언랭':
        winper = ' '
        win = '언랭'
    else:
        winper = f'({win/(win+loss)*100:.2f}%)'
        win = f'{win}승'
    if loss == ' ':
        loss = ' '
    else:
        loss = f'{loss}패'
    embed.add_field(name='승률', value=f'{win} {loss} {winper}')
    if tier == '언랭':
        tier_url = ''
    else:
        tier_url = f'https://opgg-static.akamaized.net/images/medals_new/{tier.lower()}.png?image=q_auto:best&v=1'
        embed.set_author(name= ctx.user.name, icon_url=tier_url)
    print(tier_url)

    _Rank = Rank(summoner_name)
    _Normal = Normal(summoner_name)
    _ARAM = ARAM(summoner_name)
    embed.add_field(name='솔로랭크', value='```css\n{}\n```'.format(_Rank[0]), inline = False)
    embed.add_field(name='노말', value='```css\n{}\n```'.format(_Normal[0]), inline = False)
    embed.add_field(name='무작위 총력전', value='```css\n{}\n```'.format(_ARAM[0]), inline = False)
    
    await response_msg.edit(f'```css\n검색이 완료 되었습니다.```')
    # Add recent match summaries
    match_summary = ''
    for match in recent_matches:
        champion_name = match['champion_name']
        kda = match['kda']
        gamemode = match['gamemode']
        result = '승리' if match['win'] else '패배'
        match_summary += f"\n- [{gamemode}] {champion_name}: {kda} ({result})"
    if match_summary:
        embed.add_field(name='최근 전적', value=f'```css\n{match_summary}```', inline=False)

    await ctx.channel.send(embed=embed)

# Event to handle incoming messages
@client.slash_command(name='ingame', description='소환사의 인게임 정보를 검색합니다.')
async def search_ingame(ctx, summoner_name: str  = SlashOption(description="소환사 이름을 입력해주세요.")):
    
    # Check if the message is a command and from an authorized user
    if ctx.user == client.user:
        return
    
    response_msg = await ctx.send(f'```css\n약 5초 정도 소요됩니다.```')
    
    try:
        if len(summoner_name) == 2:
            summoner_name = summoner_name[0] + ' ' + summoner_name[1]
            summoner__name = summoner_name[0] + ' ' + summoner_name[1]
        else:
            summoner_name = summoner_name
            summoner__name = summoner_name
    except TypeError:
         await response_msg.edit(f'```css\nsummoner_name을 선택하고 소환사 이름을 입력해주세요.```')
         return
       
    region = "kr"  # ex) na1, euw1
    endpoint = f"https://{region}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/"
    
    # Get summoner ID from summoner name
    summoner_url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}?api_key={API_KEY}"
    print(summoner_url)
    response = requests.get(summoner_url)
    print(response)
    if response.status_code != 200:
        await response_msg.edit(f'```css\n소환사를 찾을 수 없습니다.```')
        return
    summoner_id = response.json()['id']
    
    # Get game info from summoner ID
    game_url = endpoint + summoner_id + '?api_key=' + API_KEY
    print(game_url)
    response = requests.get(game_url)
    game_data = response.json()
    # Check if the summoner is in game
    if "status" in game_data:
        await response_msg.edit(f'```css\n게임중이 아닙니다.```')
        return
    
    # Create Embed
    embed = nextcord.Embed(title="인게임 정보", color=0x00ff00)
    for smsm in game_data['participants']:
        rank_data = get_rank(smsm['summonerId'])
        print(rank_data)
    participants = [[get_champion_name(participant['championId']), participant['summonerName'], get_rank(participant['summonerId'])] for participant in game_data['participants']]
    print(participants)
    banpick_names = []
    for bannedChampion in game_data["bannedChampions"]:
        banpick_name = get_champion_name(bannedChampion['championId'])
        banpick_names.append(banpick_name)

    # Get banpick information for each team
    red_team_bans = []
    blue_team_bans = []
    for banpick_name in banpick_names:
        if len(blue_team_bans) < 5:
            blue_team_bans.append(banpick_name)
        else:
            red_team_bans.append(banpick_name)

    # Create Embed
    embed = nextcord.Embed(title="인게임 정보", color=0x00ff00)

    game_mode = game_mode_data(game_data["gameQueueConfigId"])
    game_map = game_map_data(game_data["mapId"])
    # Add game info to the Embed
    embed.add_field(name="게임모드", value=f'```css\n[{game_mode}] {game_map}```', inline=False)


    # Add players to the Embed
    blue_team_value = ''
    red_team_value = ''
    for i, participant in enumerate(participants):
        team_id = "Blue" if i < 5 else "Red"
        print(i)
        print(participant)
        champion_name, summoner_name, tier = participant
        print(tier)
        value = f"{champion_name} ({summoner_name})"
        try:
            value2 = f"{tier['tier']} {tier['rank']} ({tier['lp']}LP)"
        except KeyError:
            value2 = '언랭'
        print(value)
        if team_id == "Red":
            red_team_value += f"{value}\n{value2}\n\n"
        else:
            blue_team_value += f"{value}\n{value2}\n\n"
    '''
    # Get observer URL
    observer_url = game_data.get("observers", {}).get("encryptionKey", "")
    '''
    
    # Send Embed
    if banpick_names:
        red_team_ban_str = '**밴픽**: ' + ', '.join(red_team_bans) if red_team_bans else ''
        blue_team_ban_str = '**밴픽**: ' + ', '.join(blue_team_bans) if blue_team_bans else ''
        embed.add_field(name='Blue team', value=f'```css\n{blue_team_value}\n{blue_team_ban_str}```', inline=True)
        embed.add_field(name='Red team', value=f'```css\n{red_team_value}\n{red_team_ban_str}```', inline=True)
    else:
        embed.add_field(name='Blue team', value=f'```css\n{blue_team_value}```', inline=True)
        embed.add_field(name='Red team', value=f'```css\n{red_team_value}```', inline=True)
        
    '''
    # Add observer URL to the Embed
    if observer_url:
        embed.add_field(name="관전 URL", value=f"spectator://kr.lol.riotgames.com:80/observer-mode/rest/encrypt/{observer_url}", inline=False)
    '''
    region = 'kr'
    summoner_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner__name}?api_key={API_KEY}'
    print(summoner_url)
    response = requests.get(summoner_url)
    print(summoner_name)
    print(response.status_code)
    if response.status_code != 200:
        await response_msg.edit(f'```css\n소환사를 찾을 수 없습니다.```')
        return
    data = json.loads(response.text)
    summoner___name = data['name']
    print(summoner___name)
    
    
    # Add OPGG link to the Embed
    re_name = summoner___name.strip().replace(' ', '%20')
    opgg_url = f'https://op.gg/summoners/{region}/{re_name}/ingame'
    embed.description = f'[OP.GG에서 {summoner___name}님의 게임 관전하기]({opgg_url})'
    
    await response_msg.edit(f'```css\n검색이 완료 되었습니다.```')
    
    await ctx.channel.send(embed=embed)
        
@client.event
async def on_ready():
    print("---------------    CONNECTED    ---------------")
    print(f"  봇 이름 : {client.user.name}")
    print(f"  봇 ID : {client.user.id}")
    print("-----------------------------------------------")

client.run(TOKEN)