#pyinstaller --onefile --icon=.\NIX.ico main.py
import logging
import asyncio
import nextcord
import requests
import json
import time
import concurrent.futures
import sqlite3
import aiohttp
from observer import observer
from nextcord.ext import commands
from nextcord import SlashOption, ButtonStyle, Interaction
from nextcord.ui import View, Button 
from MMR_API import Rank, Normal, ARAM
# from itertools import combinations
# import itertools

with open("KEY.json", "r") as f:
	data = json.load(f)

# 로그 생성
logger = logging.getLogger()

# 로그의 출력 기준 설정
logger.setLevel(logging.INFO)

# log 출력 형식
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# log 출력
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# log를 파일에 출력
file_handler = logging.FileHandler('nix.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Discord Bot Token
TOKEN = data['DISCORD_TOKEN']

# Riot API Key
API_KEY = data['RIOT_API_KEY']

intents = nextcord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)

region = 'kr'

request_header = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh-TW;q=0.5,zh;q=0.4,ja;q=0.3",
                    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://developer.riotgames.com",
                    "X-Riot-Token": API_KEY
                }

# SQLite 데이터베이스 생성 및 연결
conn = sqlite3.connect('path_LOL.db')
c = conn.cursor()

# 데이터베이스에 테이블 생성
c.execute('''CREATE TABLE IF NOT EXISTS user_data
             (user_id INTEGER PRIMARY KEY, data TEXT)''')
conn.commit()

# Function to get summoner icon URL
def get_icon(summoner_id):
    icon_url = f'https://kr.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}'
    response = requests.get(icon_url, headers=request_header)
    logger.info(f'icon_url:{icon_url}\nResponse:{response}')
    
    # Check the response code
    if response.status_code != 200:
        logger.info(f'icon_url_response_error:{response.status_code}')
        return None
    
    data = json.loads(response.text)
    icon_id = data['profileIconId']
    icon_image_url = f'http://ddragon.leagueoflegends.com/cdn/13.3.1/img/profileicon/{icon_id}.png'
    logger.info(f'icon_image:{icon_image_url}')
    return icon_image_url

# Get rank information by summoner id
def get_rank(summoner_id):
    league_url = f'https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}'
    response = requests.get(league_url, headers=request_header)
    logger.info(f'league_url:{league_url}\nresponse:{response}')

    # Check the response code
    if response.status_code != 200:
        logger.info(f'league_url_response_error:{response.status_code}')
        return None

    league_data = json.loads(response.text)
    print(f'leagudata:{league_data}')
    rank_data = {}
    for queue in league_data:
        if queue['queueType'] == 'RANKED_SOLO_5x5':
            rank_data['tier'] = queue['tier']
            rank_data['rank'] = queue['rank']
            rank_data['lp'] = queue['leaguePoints']
            rank_data['win'] = queue['wins']
            rank_data['loss'] = queue['losses']
    return rank_data if rank_data else None

def game_mode_data(mode_data):
    game_modes = {
        400: '일반',
        420: '솔로 랭크',
        430: '일반',
        440: '자유 랭크',
        450: '무작위 총력전',
        700: '격전',
        800: 'AI 대전',
        810: 'AI 대전',
        820: 'AI 대전',
        830: 'AI 대전',
        840: 'AI 대전',
        850: 'AI 대전',
        900: 'U.R.F',
        920: '포로왕',
        1020: '단일',
        1300: '돌격! 넥서스',
        1400: '궁극기 주문서',
        2000: '튜토리얼',
        2010: '튜토리얼',
        2020: '튜토리얼'
    }
    return game_modes.get(mode_data, None)

def game_map_data(map_data):
    game_maps = {
        1: '소환사의 협곡',
        2: '소환사의 협곡',
        3: '튜토리얼 맵',
        4: '뒤틀린 숲',
        8: '수정의 상처',
        10: '뒤틀린 숲',
        11: '소환사의 협곡',
        12: '칼바람 나락',
        14: '도살자의 다리',
        16: '우주 유적',
        18: '발로란 도시 공원',
        19: 'Substructure 43',
        20: 'Crash Site',
        21: 'Nexus Blitz',
        22: 'Convergence'
    }
    return game_maps.get(map_data, None)

# Function to get recent match history
def get_recent_matches(puuid, region):
    start = time.time()
    count = 10
    matches_url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}'
    response = requests.get(matches_url, headers=request_header)
    logger.info(f'matches_url:{matches_url}\nresponse:{response}')
    match_ids = json.loads(response.text)
    matches = {
        'gamemode': [],
        'champion_name': [],
        'win': [],
        'kda': [],
        'calculate_kda': []
    }
    match_data_dict = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_match_id = {}
        for match_id in match_ids:
            match_url = f'https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}'
            future = executor.submit(requests.get, match_url, headers=request_header)
            future_to_match_id[future] = match_id

        for future in concurrent.futures.as_completed(future_to_match_id):
            match_id = future_to_match_id[future]
            try:
                match_data = json.loads(future.result().text)
                match_data_dict[match_id] = match_data
            except:
                match_data_dict[match_id] = None

    for match_id in match_ids:
        if match_id in match_data_dict:
            match_data = match_data_dict[match_id]
            try:
                participant = next(p for p in match_data['info']['participants'] if p['puuid'] == puuid)
                win = '🔵' if participant['win'] else '🔴'
                champion_name = get_champion_name(participant['championId'])
                game_mode = f"{win} {game_mode_data(match_data['info']['queueId'])}"
                kda = f"{participant['kills']}/{participant['deaths']}/{participant['assists']}"
                calculate__kda = calculate_kda(participant['kills'], participant['deaths'], participant['assists'])
                
                matches['gamemode'].append(f"```css\n{game_mode}```")
                matches['champion_name'].append(f"```css\n{champion_name}```")
                matches['kda'].append(f"```css\n{kda} {calculate__kda}```")
            except (KeyError, StopIteration):
                continue

    logger.info(f'get_recent_matches_time:{time.time() - start}초\n')
    return matches

def calculate_kda(kills, deaths, assists):
    if deaths == 0:
        return f"{kills + assists}:1"
    else:
        return f"{(kills + assists) / deaths:.2f}:1"

def get_champion_name(champion_id):
    # Connect to database
    conn = sqlite3.connect('champions.db')
    c = conn.cursor()

    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS champions
                (id INT PRIMARY KEY, name TEXT)''')

    # Check if champion exists in the database
    c.execute("SELECT name FROM champions WHERE id=?", (champion_id,))
    row = c.fetchone()
    if row:
        return row[0]

    # If not, get champion data from API and insert into the database
    champion_url = f'http://ddragon.leagueoflegends.com/cdn/13.3.1/data/ko_KR/champion.json'
    response = requests.get(champion_url)
    data = json.loads(response.text)
    champion_data = data['data']
    for champion in champion_data.values():
        if int(champion['key']) == champion_id:
            champion_name = champion['name']
            c.execute("INSERT INTO champions (id, name) VALUES (?, ?)", (champion_id, champion_name))
            conn.commit()
            return champion_name

    # If no matching champion found, return 'Unknown'
    return 'Unknown'

# Event to handle incoming messages
@client.slash_command(name='rank', description='소환사의 전적을 검색합니다.')
async def search_rank(ctx, summoner_name: str = SlashOption(description='소환사 이름을 입력해주세요.')):
    logger.info(f'rank_search_user:{ctx.user}\n')
    # Check if the message is a command and from an authorized user
    if ctx.user == client.user:
        return
    
    response_msg = await ctx.send(f'```css\n약 3초 정도 소요됩니다.```')
    start = time.time()

    try:
        summoner_name = summoner_name.replace(' ', '')
        if len(summoner_name) == 2:
            summoner_name = summoner_name[0] + ' ' + summoner_name[1]
    except TypeError:
        await response_msg.edit(f'```css\nsummoner_name을 선택하고 소환사 이름을 입력해주세요.```')
        return

    region = 'kr'
    async with aiohttp.ClientSession() as session:
        summoner_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
        logger.info(f'summoner_url : {summoner_url}')
        async with session.get(summoner_url, headers=request_header) as response:
            logger.info(f'response : {response.status}')
            if response.status != 200:
                await response_msg.edit(f'```css\n소환사를 찾을 수 없습니다.```')
                return
            data = await response.json()

    summoner_name = data['name']
    summoner_id = data['id']
    puuid = data['puuid']
    icon_url = get_icon(summoner_id)
    rank_data = get_rank(summoner_id)
    print(rank_data)
    if rank_data == None:
        await response_msg.edit('```css\n소환사의 전적이 없습니다.```')
    else:
      tier = rank_data.get('tier')
      if tier is None:
          tier = '언랭'
          rank = ''
          lp = ''
          win = '언랭'
          winper = ''
          loss = ''
      else:
          tier_rank = rank_data.get('rank')
          if tier == 'MASTER':
              tier_rank = ''
          elif tier == 'GRANDMASTER':
              tier_rank = ''
          elif tier == 'CHALLENGER':
              tier_rank = ''
          rank = tier_rank
          lp = f'({rank_data.get("lp")}LP)'
          winper = f'({rank_data.get("win")/(rank_data.get("win")+rank_data.get("loss"))*100:.2f}%)'
          win = f'{rank_data.get("win")}승'
          loss = f'{rank_data.get("loss")}패'

      #MMR API 멀티스레딩
      with concurrent.futures.ThreadPoolExecutor() as executor:
          futures = [executor.submit(Rank, summoner_name),
                  executor.submit(Normal, summoner_name),
                  executor.submit(ARAM, summoner_name)]
          _Rank, _Normal, _ARAM = [f.result() for f in futures]
      
      # Create and send embed message for first page
      re_name = summoner_name.strip().replace(' ', '%20')
      opggurl= f'https://www.op.gg/summoners/kr/{re_name}/'
      embed1 = nextcord.Embed(title=summoner_name, color=nextcord.Color.blue(), url=opggurl)
      embed1.set_thumbnail(url=icon_url)
      embed1.add_field(name='랭크', value=f'```css\n{tier} {rank}{lp}\n```')
      embed1.add_field(name='승률', value=f'```css\n{win} {loss}{winper}\n```')
      embed1.add_field(name='솔로랭크', value = '```css\n{}\n```'.format(_Rank[0]), inline = False)
      embed1.add_field(name='노말', value = '```css\n{}\n```'.format(_Normal[0]), inline = False)
      embed1.add_field(name='무작위 총력전', value = '```css\n{}\n```'.format(_ARAM[0]), inline = False)
      embed1.set_footer(text='Page 1/2          #버튼 상호작용 실패시 전적 재검색')

      recent_matches = get_recent_matches(puuid, 'asia')
      if recent_matches:
          
          embed2 = nextcord.Embed(title='최근 전적', color=nextcord.Color.blue())
          embed2.set_thumbnail(url=icon_url)
          embed2.add_field(name='게임모드', value=''.join(recent_matches['gamemode']), inline=True)
          embed2.add_field(name='챔피언', value=''.join(recent_matches['champion_name']), inline=True)
          embed2.add_field(name='KDA', value=''.join(recent_matches['kda']), inline=True)
          embed2.set_footer(text='Page 2/2          #버튼 상호작용 실패시 전적 재검색')
      else:
          embed2 = nextcord.Embed(title='최근 전적', description='최근 전적이 없습니다.', color=nextcord.Color.blue())
          embed2.set_thumbnail(url=icon_url)
          embed2.set_footer(text='Page 2/2          #버튼 상호작용 실패시 전적 재검색')

      # Create pagination
      pages = [embed1, embed2]
      current_page = 0

      async def previous_callback(interaction):
          logger.info(f'previous_callback : {interaction.user}\n')
          nonlocal current_page
          current_page = max(0, current_page - 1)
          if current_page == 0:
              button_previous.disabled = True
              button_previous.style = ButtonStyle.gray
              
          button_next.disabled = False
          button_next.style = ButtonStyle.primary
          
          await sent_msg.edit(embed=pages[current_page], view=myview)

      async def next_callback(interaction):
          logger.info(f'next_callback : {interaction.user}\n')
          nonlocal current_page
          current_page = min(len(pages) - 1, current_page + 1)
          if current_page == len(pages) - 1:
              button_next.disabled = True
              button_next.style = ButtonStyle.gray
              
          button_previous.disabled = False
          button_previous.style = ButtonStyle.primary
          
          await sent_msg.edit(embed=pages[current_page], view=myview)
          
      # Define button
      button_previous = Button(label='◀️', style=ButtonStyle.gray, disabled=True)
      button_next = Button(label='▶️', style=ButtonStyle.primary)
      
      #Button CallBack
      button_previous.callback = previous_callback
      button_next.callback = next_callback
      
      myview = View(timeout=300)
      myview.add_item(button_previous)
      myview.add_item(button_next)

      # Send initial message
      sent_msg = await ctx.send(embed=embed1, view=myview)

      # Edit response message with search time
      await response_msg.edit(f'```css\n검색이 완료 되었습니다.\n{time.time() - start}초```')



# Event to handle incoming messages
@client.slash_command(name='ingame', description='소환사의 인게임 정보를 검색합니다.')
async def search_ingame(ctx, summoner_name: str  = SlashOption(description="소환사 이름을 입력해주세요.")):
    logger.info(f'ingame_search_user:{ctx.user}\n')
    start = time.time()
    # Check if the message is a command and from an authorized user
    if ctx.user == client.user:
        return
    
    response_msg = await ctx.send(f'```css\n약 5초 정도 소요됩니다.```')
    
    try:
        summoner_name = summoner_name.replace(' ', '')
        logger.info(f'공백제거 summoner_name : {summoner_name}\n')
        if len(summoner_name) == 2:
            summoner_name = summoner_name[0] + ' ' + summoner_name[1]
            logger.info(f'2자리 닉네임 공백 추가 summoner_name : {summoner_name}\n')
    except TypeError:
         await response_msg.edit(f'```css\nsummoner_name을 선택하고 소환사 이름을 입력해주세요.```')
         return
       
    region = "kr"  # ex) na1, euw1
    endpoint = f"https://{region}.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/"
    
    # Get summoner ID from summoner name
    async with aiohttp.ClientSession() as session:
        summoner_url = f'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
        logger.info(f'summoner_url : {summoner_url}')
        async with session.get(summoner_url, headers=request_header) as response:
            logger.info(f'response : {response.status}')
            if response.status != 200:
                await response_msg.edit(f'```css\n소환사를 찾을 수 없습니다.```')
                return
            data = await response.json()

    summoner_id = data['id']
    summoner__name = data['name']
    
    # Get game info from summoner ID
    game_url = endpoint + summoner_id
    logger.info(f'game_url : {game_url}')
    response = requests.get(game_url, headers=request_header)
    logger.info(f'matches_url:{game_url}\nresponse:{response}')
    game_data = json.loads(response.text)
    
    try:
        game_id = game_data["gameId"]
        logger.info(f'game_id : {game_id}')
    except:
        game_id = None
    
    # Check if the summoner is in game
    if "status" in game_data:
        await response_msg.edit(f'```css\n게임중이 아닙니다.```')
        return
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Run get_rank for each participant in a separate thread
        futures = []
        for smsm in game_data['participants']:
            future = executor.submit(get_rank, smsm['summonerId'])
            futures.append(future)

        # Get the results of each thread and log them
        for future in concurrent.futures.as_completed(futures):
            rank_data = future.result()
            logger.info(f'rank_data : {rank_data}')

        # Get participant information for each participant in a separate thread
        futures = []
        for participant in game_data['participants']:
            future = executor.submit(get_champion_name, participant['championId'])
            futures.append(future)

        # Get the results of each thread and create the participants list
        participants = []
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            champion_name = future.result()
            summoner_name = game_data['participants'][i]['summonerName']
            rank = get_rank(game_data['participants'][i]['summonerId'])
            participants.append([champion_name, summoner_name, rank])
        logger.info(f'participants : {participants}')

        # Get banpick information for each banned champion in a separate thread
        futures = []
        for bannedChampion in game_data["bannedChampions"]:
            future = executor.submit(get_champion_name, bannedChampion['championId'])
            futures.append(future)

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

        # Wait for all threads to complete
        concurrent.futures.wait(futures)

    # Create Embed
    embed = nextcord.Embed(title="인게임 정보", color=0x00ff00)

    game_mode = game_mode_data(game_data["gameQueueConfigId"])
    game_map = game_map_data(game_data["mapId"])
    
    # Add game info to the Embed
    embed.add_field(name="게임모드", value=f'```css\n[{game_mode}] {game_map}```', inline=False)


    # Add players to the Embed
    blue_team_value = ''
    red_team_value = ''
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_rank, participant['summonerId']) for participant in game_data['participants']]
        for i, participant in enumerate(game_data['participants']):
            team_id = "Blue" if i < 5 else "Red"
            champion_name, summoner_name = get_champion_name(participant['championId']), participant['summonerName']
            tier = futures[i].result()
            summoner_name = summoner_name.strip()
            value = f"{champion_name} ({summoner_name})"
            try:
                tier_tier = tier['tier']
                
                try:
                    tier_rank = tier['rank']
                    tier_lp = tier['lp']
                    if tier_tier == 'MASTER':
                        tier_rank = ''
                    elif tier_tier == 'GRANDMASTER':
                        tier_rank = ''
                    elif tier_tier == 'CHALLENGER':
                        tier_rank = ''
                        
                except TypeError:
                    tier_rank = '언랭'
                    
            except TypeError:
                tier_tier = '언랭'
                
            try:
                if tier_tier == '언랭':
                    value2 = "언랭"
                else:
                    value2 = f"{tier_tier} {tier_rank}({tier_lp}LP)"
            except KeyError:
                value2 = '언랭'
            if team_id == "Red":
                red_team_value += f"{value}\n{value2}\n\n"
            else:
                blue_team_value += f"{value}\n{value2}\n\n"
    
    # Send Embed
    if banpick_names:
        red_team_ban_str = '**밴픽**: ' + ', '.join(red_team_bans) if red_team_bans else ''
        blue_team_ban_str = '**밴픽**: ' + ', '.join(blue_team_bans) if blue_team_bans else ''
        embed.add_field(name='Blue team', value=f'```css\n{blue_team_value}\n{blue_team_ban_str}```', inline=True)
        embed.add_field(name='Red team', value=f'```css\n{red_team_value}\n{red_team_ban_str}```', inline=True)
    else:
        embed.add_field(name='Blue team', value=f'```css\n{blue_team_value}```', inline=True)
        embed.add_field(name='Red team', value=f'```css\n{red_team_value}```', inline=True)
                
    # Add OPGG link to the Embed
    re_name = summoner__name.strip().replace(' ', '%20')
    opgg_url = f'https://op.gg/summoners/{region}/{re_name}/ingame'
    embed.description = f'[OP.GG에서 {summoner__name}님의 인게임 정보 보기]({opgg_url})'
    
    # Get observer URL
    encryptionKey = game_data.get("observers", {}).get("encryptionKey", "")
    logger.info(f'encryptionKey : {encryptionKey}')
    
    # Add observer URL to the Embed
    if encryptionKey:
        user_id = ctx.user.id
        
        # Check if there is already a record for the user
        c.execute("SELECT * FROM user_data WHERE user_id=?", (user_id,))
        existing_data = c.fetchone()
        
        if existing_data:
            # If there is an existing record, use the stored game path
            game_path = existing_data[1]
        else:
            # If there is no existing record, use the default game path
            game_path = 'C:\\Riot Games\\League of Legends'
        embed.set_footer(text = '관전을 하시려면 아래 파일을 다운로드 후 실행하세요!\n\n롤의 설치 경로가 기본 설치 경로가 아니라면 "/get_path" 커맨드를 이용해 롤 설치된 경로를 쉽게 알아낼 수 있습니다.\n당연히 바이러스가 없지만 사용하기 꺼려하시는 사용자는 직접 롤 경로를 "/path" 커맨드에 입력 하시면 됩니다.\n"/path" 경로 입력 예시:\nC:\Riot Games\League of Legends (이 경로가 기본 설치 경로 입니다.)\n경로를 한번 설정하면 다시 경로 설정 할 필요 없습니다.')
        await observer(encryptionKey, game_id, game_path)
        print(game_id)
        observer_file = nextcord.File(f'NIX_OBSERVER_{game_id}.bat')
        
        
    await ctx.channel.send(embed=embed)
    await response_msg.edit(f'```css\n검색이 완료 되었습니다.\n{time.time() - start}초```')
    
    if observer_file:
        await ctx.channel.send(file=observer_file)
           
    logger.info(f'search_ingame_time : {time.time() - start}')


# 들어오는 메시지 처리 이벤트
@client.slash_command(name='path', description='롤 설치 경로를 설정합니다.')
async def save_game_path(ctx, gamepath: str = SlashOption(description='롤 설치 경로를 입력해주세요.')):
    logger.info(f'save_game_path_user:{ctx.user}\n')
    
    # 메시지가 명령어이고 인증된 사용자에서 왔는지 확인합니다
    if ctx.user == client.user:
        return
    
    # 응답 메시지를 보냅니다
    start = time.time()
    response_msg = await ctx.send('```css\n잠시만 기다려주세요.```')
    
    async def save_path():
        # 사용자 ID와 입력된 데이터를 변수에 저장합니다
        user_id = ctx.user.id
        data = gamepath
        
        # 사용자에 대한 레코드가 이미 있는지 확인합니다
        c.execute("SELECT * FROM user_data WHERE user_id=?", (user_id,))
        existing_data = c.fetchone()
        
        if existing_data:
            # 레코드가 이미 있다면 데이터 열을 업데이트합니다
            c.execute("UPDATE user_data SET data=? WHERE user_id=?", (data, user_id))
        else:
            # 레코드가 없다면 새로운 레코드를 삽입합니다
            c.execute("INSERT INTO user_data (user_id, data) VALUES (?, ?)", (user_id, data))
        
        conn.commit()
    
    await asyncio.gather(save_path(), response_msg.edit(f'```css\n데이터베이스에 저장 되었습니다.\n{time.time() - start}초```'))

# 들어오는 메시지 처리 이벤트
@client.slash_command(name='path_reset', description='롤 설치 경로를 초기화 합니다.')
async def save_game_path(ctx):
    logger.info(f'save_game_path_user:{ctx.user}\n')
    
    # 메시지가 명령어이고 인증된 사용자에서 왔는지 확인합니다
    if ctx.user == client.user:
        return
    
    # 응답 메시지를 보냅니다
    start = time.time()
    response_msg = await ctx.send('```css\n잠시만 기다려주세요.```')
    
    async def save_path():
        # 사용자 ID와 입력된 데이터를 변수에 저장합니다
        user_id = ctx.user.id
        data = 'C:\Riot Games\League of Legends'
        
        # 사용자에 대한 레코드가 이미 있는지 확인합니다
        c.execute("SELECT * FROM user_data WHERE user_id=?", (user_id,))
        existing_data = c.fetchone()
        
        if existing_data:
            # 레코드가 이미 있다면 데이터 열을 업데이트합니다
            c.execute("UPDATE user_data SET data=? WHERE user_id=?", (data, user_id))
        else:
            # 레코드가 없다면 새로운 레코드를 삽입합니다
            c.execute("INSERT INTO user_data (user_id, data) VALUES (?, ?)", (user_id, data))
        
        conn.commit()
    
    await asyncio.gather(save_path(), response_msg.edit(f'```css\n데이터베이스에 저장 되었습니다.\n{time.time() - start}초```'))

# 들어오는 메시지 처리 이벤트
@client.slash_command(name='get_path', description='롤 설치 경로를 자동으로 검색하는 프로그램을 다운로드 합니다.')
async def save_game_path(ctx):
    logger.info(f'save_game_path_user:{ctx.user}\n')
    
    # 메시지가 명령어이고 인증된 사용자에서 왔는지 확인합니다
    if ctx.user == client.user:
        return
    
    # 응답 메시지를 보냅니다
    await ctx.send('```css\n아래 링크에서 파일을 다운받고 압축을 풀고 main.exe를 실행 후 검색을 누르고 기다리면 롤의 경로가 검색됩니다.\n검색된 경로를 클릭하면 복사됩니다.\n그 후 디스코드에서 /path 에 복사된 경로를 붙여 넣습니다.```')
    await ctx.send('http://dbserver.dothome.co.kr/%EA%B2%BD%EB%A1%9C_%EA%B2%80%EC%83%89.zip')
    return

# 구현 중
# balance 함수 정의
# 소환사 랭크 정보 조회 함수를 구현합니다
async def balance(summoner_names):
    summoner_tiers = {}
    print(summoner_names)
    # 소환사 이름을 순회하며 티어 정보 조회
    async with aiohttp.ClientSession() as session:
        for name in summoner_names:
            print(name)
            summoner_url = f'https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}'
            print(summoner_url)
            async with session.get(summoner_url, headers=request_header) as response:
                if response.status != 200:
                    print(response.status)
                    return f'소환사 {name}을(를) 찾을 수 없습니다.'

                try:
                    data = await response.json()
                    summoner_id = data['id']

                    # 소환사 ID로 티어 정보 조회
                    rank_data = get_rank(summoner_id)
                    if rank_data:
                        tier = rank_data['tier']
                        summoner_tiers[name] = tier
                    else:
                        summoner_tiers[name] = '언랭'
                except Exception as e:
                    return f'소환사 {name}의 정보를 가져오는 중에 오류가 발생했습니다.\n{e}'

    # 티어를 기준으로 소환사들을 밸런스 맞춰 팀을 구성
     # 티어를 기준으로 소환사들을 밸런스 맞춰 팀을 구성
    summoners_sorted = sorted(summoner_tiers, key=lambda x: summoner_tiers[x])

    # 팀을 두 개로 분할
    team1, team2 = [], []
    for index, name in enumerate(summoners_sorted):
        if index % 2 == 0:
            team1.append(name)
        else:
            team2.append(name)

    # 팀의 티어 평균 계산
    def calculate_team_tier_average(team):
        return sum(map(lambda x: summoner_tiers[x], team)) / len(team)

    # 팀의 티어 불균형 최소화를 위해 팀을 재조정
    while abs(calculate_team_tier_average(team1) - calculate_team_tier_average(team2)) > 1:
        if calculate_team_tier_average(team1) > calculate_team_tier_average(team2):
            # 팀 1에서 가장 높은 티어를 팀 2로 이동
            team1_tiers = [summoner_tiers[name] for name in team1]
            max_tier_index = team1_tiers.index(max(team1_tiers))
            team2.append(team1.pop(max_tier_index))
        else:
            # 팀 2에서 가장 높은 티어를 팀 1로 이동
            team2_tiers = [summoner_tiers[name] for name in team2]
            max_tier_index = team2_tiers.index(max(team2_tiers))
            team1.append(team2.pop(max_tier_index))

    # Embed 생성
    embed = nextcord.Embed(title="팀 밸런스", color=0x00ff00)
    embed.add_field(name="팀 1", value="\n".join(team1), inline=True)
    embed.add_field(name="팀 2", value="\n".join(team2), inline=True)

    return embed

# 구현 중
# balance 커맨드 정의
@client.slash_command(name='balance', description='소환사들의 팀 밸런스를 계산합니다.')
async def balance_teams(ctx, summoner1: str, summoner2: str, summoner3: str, summoner4: str, summoner5: str,
                       summoner6: str, summoner7: str, summoner8: str, summoner9: str, summoner10: str):
    summoner_names = [summoner1, summoner2, summoner3, summoner4, summoner5, summoner6, summoner7, summoner8,
                      summoner9, summoner10]
    response_msg = await ctx.send('```css\n잠시만 기다려주세요.```')
    result = await balance(summoner_names)
    if isinstance(result, str):
        await ctx.send(result)
    else:
        await ctx.send(embed=result)

@client.event
async def on_ready():
    print("---------------    CONNECTED    ---------------")
    print(f"  봇 이름 : {client.user.name}")
    print(f"  봇 ID : {client.user.id}")
    print("-----------------------------------------------")

async def main():
    await client.start(TOKEN)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
