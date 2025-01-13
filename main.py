import asyncio
import os
import socket
import sys
import time
import traceback

import requests
import urllib3
from colr import color as colr
from InquirerPy import inquirer
from rich.console import Console as RichConsole

from src.colors import Colors
from src.config import Config
from src.configurator import configure
from src.constants import *
from src.content import Content
from src.errors import Error
from src.Loadouts import Loadouts
from src.logs import Logging
from src.names import Names
from src.player_stats import PlayerStats
from src.presences import Presences
from src.rank import Rank
from src.requestsV import Requests
from src.rpc import Rpc
from src.server import Server
from src.states.coregame import Coregame
from src.states.menu import Menu
from src.states.pregame import Pregame
from src.stats import Stats
from src.table import Table
from src.websocket import Ws
from src.os import get_os

from src.account_manager.account_manager import AccountManager
from src.account_manager.account_config import AccountConfig
from src.account_manager.account_auth import AccountAuth

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

os.system(f"title VALORANT rank yoinker v{version}")

server = ""


def program_exit(status: int):  # so we don't need to import the entire sys module
    log(f"exited program with error code {status}")
    raise sys.exit(status)

def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.254.254.254', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

try:
    Logging = Logging()
    log = Logging.log

    # OS Logging
    log(f"Operating system: {get_os()}\n")
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--config":
            configure()
            run_app = inquirer.confirm(
                message="Do you want to run vRY now?", default=True
            ).execute()
            if run_app:
                os.system('cls')
            else:
                os._exit(0)
        else:
            os.system('cls')
    except Exception as e:
        print("Something went wrong while running configurator!")
        log(f"configurator encountered an error")
        log(str(traceback.format_exc()))
        input("press enter to exit...\n")
        os._exit(1)

    acc_manager = AccountManager(log, AccountConfig, AccountAuth, NUMBERTORANKS)

    ErrorSRC = Error(log, acc_manager)

    Requests.check_version(version, Requests.copy_run_update_script)
    Requests.check_status()
    Requests = Requests(version, log, ErrorSRC)

    cfg = Config(log)

    content = Content(Requests, log)

    rank = Rank(Requests, log, content, before_ascendant_seasons)
    pstats = PlayerStats(Requests, log, cfg)

    namesClass = Names(Requests, log)

    presences = Presences(Requests, log)


    menu = Menu(Requests, log, presences)
    pregame = Pregame(Requests, log)
    coregame = Coregame(Requests, log)

    Server = Server(log, ErrorSRC)
    Server.start_server()


    agent_dict = content.get_all_agents()

    map_info = content.get_all_maps()
    map_urls = content.get_map_urls(map_info)
    map_splashes = content.get_map_splashes(map_info)

    current_map = coregame.get_current_map(map_urls, map_splashes)

    colors = Colors(hide_names, agent_dict, AGENTCOLORLIST)

    loadoutsClass = Loadouts(Requests, log, colors, Server, current_map)
    table = Table(cfg, log)

    stats = Stats()

    if cfg.get_feature_flag("discord_rpc"):
        rpc = Rpc(map_urls, gamemodes, colors, log)
    else:
        rpc = None

    Wss = Ws(Requests.lockfile, Requests, cfg, colors, hide_names, Server, rpc)
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_forever()

    log(f"VALORANT rank yoinker v{version}")


    valoApiSkins = requests.get("https://valorant-api.com/v1/weapons/skins")
    gameContent = content.get_content()
    seasonID = content.get_latest_season_id(gameContent)
    previousSeasonID = content.get_previous_season_id(gameContent)
    lastGameState = ""

    print("\nvRY Mobile", color(f"- {get_ip()}:{cfg.port}", fore=(255, 127, 80)))

    print(color("\nVisit https://vry.netlify.app/matchLoadouts to view full player inventories\n", fore=(255, 253, 205)))


    richConsole = RichConsole()


    firstTime = True
    firstPrint = True
    while True:
        table.clear()
        table.set_default_field_names()
        table.reset_runtime_col_flags()

        try:


            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(Wss.conntect_to_websocket())
            # if firstTime:
            #     loop = asyncio.new_event_loop()
            #     asyncio.set_event_loop(loop)
            #     game_state = loop.run_until_complete(Wss.conntect_to_websocket(game_state))
            if firstTime:
                run = True
                while run:
                    while True:
                        presence = presences.get_presence()
                        #wait until your own valorant presence is initialized
                        if presences.get_private_presence(presence) != None:
                            break
                        time.sleep(5)
                    if cfg.get_feature_flag("discord_rpc"):
                        rpc.set_rpc(presences.get_private_presence(presence))
                    game_state = presences.get_game_state(presence)
                    if game_state != None:
                        run = False
                    time.sleep(2)
                log(f"first game state: {game_state}")
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                previous_game_state = game_state
                game_state = loop.run_until_complete(Wss.recconect_to_websocket(game_state))
                # We invalidate the cached responses when going from any state to menus
                if previous_game_state != game_state and game_state == "MENUS":
                    rank.invalidate_cached_responses()
                log(f"new game state: {game_state}")
                loop.close()
            firstTime = False
            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # loop.run_until_complete()
        except TypeError:
            raise Exception("Game has not started yet!")
        # if cfg.cooldown == 0 or game_state != lastGameState:
        if True:
            log(f"getting new {game_state} scoreboard")
            lastGameState = game_state
            game_state_dict = {
                "INGAME": color('In-Game', fore=(241, 39, 39)),
                "PREGAME": color('Agent Select', fore=(103, 237, 76)),
                "MENUS": color('In-Menus', fore=(238, 241, 54)),
            }

            if (not firstPrint) and cfg.get_feature_flag("pre_cls"):
                    os.system('cls')

            is_leaderboard_needed = False

            priv_presence = presences.get_private_presence(presence)
            if priv_presence["provisioningFlow"] == "CustomGame" or priv_presence["partyState"] == "CUSTOM_GAME_SETUP":
                gamemode = "Custom Game"
            else:
                gamemode = gamemodes.get(priv_presence['queueId'])

            heartbeat_data = {
                "time": int(time.time()),
                "state": game_state,
                "mode": gamemode,
                "puuid": Requests.puuid,
                "players": {}
            }

            if game_state == "INGAME":
                coregame_stats = coregame.get_coregame_stats()
                if coregame_stats == None:
                    continue
                Players = coregame_stats["Players"]
                #data for chat to function
                presence = presences.get_presence()
                partyMembers = menu.get_party_members(Requests.puuid, presence)
                partyMembersList = [a["Subject"] for a in partyMembers]

                players_data = {}
                players_data.update({"ignore": partyMembersList})
                for player in Players:
                    if player["Subject"] == Requests.puuid:
                        if cfg.get_feature_flag("discord_rpc"):
                            rpc.set_data({"agent": player["CharacterID"]})
                    players_data.update({player["Subject"]: {"team": player["TeamID"], "agent": player["CharacterID"], "streamer_mode": player["PlayerIdentity"]["Incognito"]}})
                Wss.set_player_data(players_data)

                try:
                    server = GAMEPODS[coregame_stats["GamePodID"]]
                except KeyError:
                    server = "New server"
                presences.wait_for_presence(namesClass.get_players_puuid(Players))
                names = namesClass.get_names_from_puuids(Players)
                loadouts_arr = loadoutsClass.get_match_loadouts(coregame.get_coregame_match_id(), Players, cfg.weapon, valoApiSkins, names, state="game")
                loadouts = loadouts_arr[0]
                loadouts_data = loadouts_arr[1]
                # with alive_bar(total=len(Players), title='Fetching Players', bar='classic2') as bar:
                isRange = False
                playersLoaded = 1
                
                heartbeat_data["map"] = map_urls[coregame_stats["MapID"].lower()],
                with richConsole.status("Loading Players...") as status: 
                    partyOBJ = menu.get_party_json(namesClass.get_players_puuid(Players), presence)
                    # log(f"retrieved names dict: {names}")
                    Players.sort(key=lambda Players: Players["PlayerIdentity"].get("AccountLevel"), reverse=True)
                    Players.sort(key=lambda Players: Players["TeamID"], reverse=True)
                    partyCount = 0
                    partyNum = 0
                    partyIcons = {}
                    lastTeamBoolean = False
                    lastTeam = "Red"


                    already_played_with = []
                    stats_data = stats.read_data()

                    for p in Players:
                        if p["Subject"] == Requests.puuid:
                            allyTeam = p["TeamID"]
                            break
                    for player in Players:
                        # used to change player name color
                        already_seen = False
                        status.update(f"Loading players... [{playersLoaded}/{len(Players)}]")
                        playersLoaded += 1

                        if player["Subject"] in stats_data.keys():
                            if player["Subject"] != Requests.puuid and player["Subject"] not in partyMembersList:
                                curr_player_stat = stats_data[player["Subject"]][-1]
                                i = 1
                                while curr_player_stat["match_id"] == coregame.match_id and len(stats_data[player["Subject"]]) > i:
                                    i+=1
                                # if curr_player_stat["match_id"] == coregame.match_id and len(stats_data[player["Subject"]]) > 1:
                                    curr_player_stat = stats_data[player["Subject"]][-i]
                                if curr_player_stat["match_id"] != coregame.match_id:
                                    #checking for party memebers and self players
                                    times = 0
                                    m_set = ()
                                    for m in stats_data[player["Subject"]]:
                                        if m["match_id"] != coregame.match_id and m["match_id"] not in m_set:
                                            times += 1
                                            m_set += (m["match_id"],)
                                    if player["PlayerIdentity"]["Incognito"] == False:
                                        already_played_with.append(
                                                {
                                                    "times": times,
                                                    "name": curr_player_stat["name"],
                                                    "agent": curr_player_stat["agent"],
                                                    "time_diff": time.time() - curr_player_stat["epoch"]
                                                })
                                        # used to change player name color
                                        already_seen = True
                                    else:
                                        if player["TeamID"] == allyTeam:
                                            team_string = "your"
                                        else:
                                            team_string = "enemy"
                                        already_played_with.append(
                                                {
                                                    "times": times,
                                                    "name": agent_dict[player["CharacterID"].lower()] + " on " + team_string + " team",
                                                    "agent": curr_player_stat["agent"],
                                                    "time_diff": time.time() - curr_player_stat["epoch"]
                                                })
                                        # used to change player name color
                                        already_seen = True

                        party_icon = ''
                        # set party premade icon
                        for party in partyOBJ:
                            if player["Subject"] in partyOBJ[party]:
                                if party not in partyIcons:
                                    partyIcons.update({party: PARTYICONLIST[partyCount]})
                                    # PARTY_ICON
                                    party_icon = PARTYICONLIST[partyCount]
                                    partyNum = partyCount + 1
                                    partyCount += 1
                                else:
                                    # PARTY_ICON
                                    party_icon = partyIcons[party]
                        playerRank = rank.get_rank(player["Subject"], seasonID)
                        previousPlayerRank = rank.get_rank(player["Subject"], previousSeasonID)

                        if player["Subject"] == Requests.puuid:
                            if cfg.get_feature_flag("discord_rpc"):
                                rpc.set_data({"rank": playerRank["rank"], "rank_name": colors.escape_ansi(NUMBERTORANKS[playerRank["rank"]]) + " | " + str(playerRank["rr"]) + "rr"})
                        # rankStatus = playerRank[1]
                        #useless code since rate limit is handled in the requestsV
                        # while not rankStatus:
                        #     print("You have been rate limited, 😞 waiting 10 seconds!")
                        #     time.sleep(10)
                        #     playerRank = rank.get_rank(player["Subject"], seasonID)
                        #     rankStatus = playerRank[1]

                        ppstats = pstats.get_stats(player["Subject"])
                        hs = ppstats["hs"]
                        kd = ppstats["kd"]

                        player_level = player["PlayerIdentity"].get("AccountLevel")



                        if player["PlayerIdentity"]["Incognito"]:
                            Namecolor = colors.get_color_from_team(player["TeamID"],
                                                            names[player["Subject"]],
                                                            player["Subject"],
                                                            Requests.puuid,
                                                            agent=player["CharacterID"],
                                                            party_members=partyMembersList,
                                                            played_before=already_seen)
                        else:
                            Namecolor = colors.get_color_from_team(player["TeamID"],
                                                            names[player["Subject"]],
                                                            player["Subject"],
                                                            Requests.puuid,
                                                            party_members=partyMembersList,
                                                            played_before=already_seen)
                        if lastTeam != player["TeamID"]:
                            if lastTeamBoolean:
                                table.add_empty_row()
                        lastTeam = player['TeamID']
                        lastTeamBoolean = True
                        if player["PlayerIdentity"]["HideAccountLevel"]:
                            if player["Subject"] == Requests.puuid or player["Subject"] in partyMembersList or hide_levels == False:
                                PLcolor = colors.level_to_color(player_level)
                            else:
                                PLcolor = ""
                        else:
                            PLcolor = colors.level_to_color(player_level)
                        # AGENT
                        # agent = str(agent_dict.get(player["CharacterID"].lower()))
                        agent = colors.get_agent_from_uuid(player["CharacterID"].lower())
                        if agent == "" and len(Players) == 1:
                            isRange = True

                        # NAME
                        name = Namecolor

                        # VIEWS
                        # views = get_views(names[player["Subject"]])

                        # skin
                        skin = loadouts[player["Subject"]]

                        # RANK
                        rankName = NUMBERTORANKS[playerRank["rank"]]
                        if cfg.get_feature_flag("aggregate_rank_rr") and cfg.table.get("rr"):
                            rankName += f" ({playerRank['rr']})"

                        # RANK RATING
                        rr = playerRank["rr"]

                        #short peak rank string
                        has_letter = any(c.isalpha() for c in str(playerRank['peakrankep']))
                        peakRankAct = f" ({playerRank['peakrankep']}a{playerRank['peakrankact']})" if has_letter else f" (e{playerRank['peakrankep']}a{playerRank['peakrankact']})"
                        if not cfg.get_feature_flag("peak_rank_act"):
                            peakRankAct = ""


                        # PEAK RANK
                        peakRank = NUMBERTORANKS[playerRank["peakrank"]] + peakRankAct

                        # PREVIOUS RANK
                        previousRank = NUMBERTORANKS[previousPlayerRank["rank"]]

                        # LEADERBOARD
                        leaderboard = playerRank["leaderboard"]

                        hs = colors.get_hs_gradient(hs)
                        wr = colors.get_wr_gradient(playerRank["wr"]) + f" ({playerRank['numberofgames']})"

                        if(int(leaderboard)>0):
                            is_leaderboard_needed = True

                        # LEVEL
                        level = PLcolor
                        table.add_row_table([party_icon,
                                              agent,
                                              name,
                                              # views,
                                              skin,
                                              rankName,
                                              rr,
                                              peakRank,
                                              previousRank,
                                              leaderboard,
                                              hs,
                                              wr,
                                              kd,
                                              level
                                              ])

                        heartbeat_data["players"][player["Subject"]] = {
                            "puuid": player["Subject"],
                            "name": names[player["Subject"]],
                            "partyNumber": partyNum if party_icon != "" else 0,
                            "agent": agent_dict[player["CharacterID"].lower()],
                            "rank": playerRank["rank"],
                            "peakRank": playerRank["peakrank"],
                            "peakRankAct": peakRankAct,
                            "rr": rr,
                            "kd": ppstats["kd"],
                            "headshotPercentage": ppstats["hs"],
                            "winPercentage": f"{playerRank['wr']} ({playerRank['numberofgames']})",
                            "level": player_level,
                            "agentImgLink": loadouts_data["Players"][player["Subject"]].get("Agent",None),
                            "team": loadouts_data["Players"][player["Subject"]].get("Team",None),
                            "sprays": loadouts_data["Players"][player["Subject"]].get("Sprays",None),
                            "title": loadouts_data["Players"][player["Subject"]].get("Title",None),
                            "playerCard": loadouts_data["Players"][player["Subject"]].get("PlayerCard",None),
                            "weapons": loadouts_data["Players"][player["Subject"]].get("Weapons",None)
                        }                     

                        stats.save_data(
                            {
                                player["Subject"]: {
                                    "name": names[player["Subject"]],
                                    "agent": agent_dict[player["CharacterID"].lower()],
                                    "map": current_map,
                                    "rank": playerRank["rank"],
                                    "rr": rr,
                                    "match_id": coregame.match_id,
                                    "epoch": time.time(),
                                }
                            }
                        )
                        # bar()
            elif game_state == "PREGAME":
                already_played_with = []
                pregame_stats = pregame.get_pregame_stats()
                if pregame_stats == None:
                    continue
                try:
                    server = GAMEPODS[pregame_stats["GamePodID"]]
                except KeyError:
                    server = "New server"
                Players = pregame_stats["AllyTeam"]["Players"]
                presences.wait_for_presence(namesClass.get_players_puuid(Players))
                names = namesClass.get_names_from_puuids(Players)
                #temporary until other regions gets fixed?
                # loadouts = loadoutsClass.get_match_loadouts(pregame.get_pregame_match_id(), pregame_stats, cfg.weapon, valoApiSkins, names,
                                            #   state="pregame")
                playersLoaded = 1
                with richConsole.status("Loading Players...") as status:
                # with alive_bar(total=len(Players), title='Fetching Players', bar='classic2') as bar:
                    presence = presences.get_presence()
                    partyOBJ = menu.get_party_json(namesClass.get_players_puuid(Players), presence)
                    partyMembers = menu.get_party_members(Requests.puuid, presence)
                    partyMembersList = [a["Subject"] for a in partyMembers]
                    # log(f"retrieved names dict: {names}")
                    Players.sort(key=lambda Players: Players["PlayerIdentity"].get("AccountLevel"), reverse=True)
                    partyCount = 0
                    partyIcons = {}
                    for player in Players:
                        status.update(f"Loading players... [{playersLoaded}/{len(Players)}]")
                        playersLoaded += 1
                        party_icon = ''

                        # set party premade icon
                        for party in partyOBJ:
                            if player["Subject"] in partyOBJ[party]:
                                if party not in partyIcons:
                                    partyIcons.update({party: PARTYICONLIST[partyCount]})
                                    # PARTY_ICON
                                    party_icon = PARTYICONLIST[partyCount]
                                    partyNum = partyCount + 1
                                else:
                                    # PARTY_ICON
                                    party_icon = partyIcons[party]
                                partyCount += 1
                        playerRank = rank.get_rank(player["Subject"], seasonID)
                        previousPlayerRank = rank.get_rank(player["Subject"], previousSeasonID)

                        if player["Subject"] == Requests.puuid:
                            if cfg.get_feature_flag("discord_rpc"):
                                rpc.set_data({"rank": playerRank["rank"], "rank_name": colors.escape_ansi(NUMBERTORANKS[playerRank["rank"]]) + " | " + str(playerRank["rr"]) + "rr"})
                        # rankStatus = playerRank[1]
                        #useless code since rate limit is handled in the requestsV
                        # while not rankStatus:
                        #     print("You have been rate limited, 😞 waiting 10 seconds!")
                        #     time.sleep(10)
                        #     playerRank = rank.get_rank(player["Subject"], seasonID)
                        #     rankStatus = playerRank[1]
                        # playerRank = playerRank[0]

                        ppstats = pstats.get_stats(player["Subject"])
                        hs = ppstats["hs"]
                        kd = ppstats["kd"]

                        player_level = player["PlayerIdentity"].get("AccountLevel")
                        if player["PlayerIdentity"]["Incognito"]:
                            NameColor = colors.get_color_from_team(pregame_stats['Teams'][0]['TeamID'],
                                                            names[player["Subject"]],
                                                            player["Subject"], Requests.puuid, agent=player["CharacterID"], party_members=partyMembersList)
                        else:
                            NameColor = colors.get_color_from_team(pregame_stats['Teams'][0]['TeamID'],
                                                            names[player["Subject"]],
                                                            player["Subject"], Requests.puuid, party_members=partyMembersList)

                        if player["PlayerIdentity"]["HideAccountLevel"]:
                            if player["Subject"] == Requests.puuid or player["Subject"] in partyMembersList or hide_levels == False:
                                PLcolor = colors.level_to_color(player_level)
                            else:
                                PLcolor = ""
                        else:
                            PLcolor = colors.level_to_color(player_level)
                        if player["CharacterSelectionState"] == "locked":
                            agent_color = color(str(agent_dict.get(player["CharacterID"].lower())),
                                                fore=(255, 255, 255))
                        elif player["CharacterSelectionState"] == "selected":
                            agent_color = color(str(agent_dict.get(player["CharacterID"].lower())),
                                                fore=(128, 128, 128))
                        else:
                            agent_color = color(str(agent_dict.get(player["CharacterID"].lower())), fore=(54, 53, 51))

                        # AGENT
                        agent = agent_color

                        # NAME
                        name = NameColor

                        # VIEWS
                        # views = get_views(names[player["Subject"]])

                        #temporary until other regions gets fixed?
                        # skin
                        # skin = loadouts[player["Subject"]]

                        # RANK
                        rankName = NUMBERTORANKS[playerRank["rank"]]
                        if cfg.get_feature_flag("aggregate_rank_rr") and cfg.table.get("rr"):
                            rankName += f" ({playerRank['rr']})"

                        # RANK RATING
                        rr = playerRank["rr"]

                        #short peak rank string
                        has_letter = any(c.isalpha() for c in str(playerRank['peakrankep']))
                        peakRankAct = f" ({playerRank['peakrankep']}a{playerRank['peakrankact']})" if has_letter else f" (e{playerRank['peakrankep']}a{playerRank['peakrankact']})"
                        if not cfg.get_feature_flag("peak_rank_act"):
                            peakRankAct = ""
                        # PEAK RANK
                        peakRank = NUMBERTORANKS[playerRank["peakrank"]] + peakRankAct

                        # PREVIOUS RANK
                        previousRank = NUMBERTORANKS[previousPlayerRank["rank"]]

                        # LEADERBOARD
                        leaderboard = playerRank["leaderboard"]

                        hs = colors.get_hs_gradient(hs)
                        wr = colors.get_wr_gradient(playerRank["wr"]) + f" ({playerRank['numberofgames']})"

                        if(int(leaderboard)>0):
                            is_leaderboard_needed = True

                        # LEVEL
                        level = PLcolor

                        table.add_row_table([party_icon,
                                              agent,
                                              name,
                                              # views,
                                              "",
                                              rankName,
                                              rr,
                                              peakRank,
                                              previousRank,
                                              leaderboard,
                                              hs,
                                              wr,
                                              kd,
                                              level,
                                              ])

                        heartbeat_data["players"][player["Subject"]] = {
                            "name": names[player["Subject"]],
                            "partyNumber": partyNum if party_icon != "" else 0,
                            "agent": agent_dict[player["CharacterID"].lower()],
                            "rank": playerRank["rank"],
                            "peakRank": playerRank["peakrank"],
                            "peakRankAct": peakRankAct,
                            "level": player_level,
                            "rr": rr,
                            "kd": ppstats["kd"],
                            "headshotPercentage": ppstats["hs"],
                            "winPercentage": f"{playerRank['wr']} ({playerRank['numberofgames']})",
                        }

                        # bar()
            if game_state == "MENUS":
                already_played_with = []
                Players = menu.get_party_members(Requests.puuid, presence)
                names = namesClass.get_names_from_puuids(Players)
                playersLoaded = 1
                with richConsole.status("Loading Players...") as status:
                # with alive_bar(total=len(Players), title='Fetching Players', bar='classic2') as bar:
                    # log(f"retrieved names dict: {names}")
                    Players.sort(key=lambda Players: Players["PlayerIdentity"].get("AccountLevel"), reverse=True)
                    seen = []
                    for player in Players:

                        if player not in seen:
                            status.update(f"Loading players... [{playersLoaded}/{len(Players)}]")
                            playersLoaded += 1
                            party_icon = PARTYICONLIST[0]
                            playerRank = rank.get_rank(player["Subject"], seasonID)
                            previousPlayerRank = rank.get_rank(player["Subject"], previousSeasonID)
                            if player["Subject"] == Requests.puuid:
                                if cfg.get_feature_flag("discord_rpc"):
                                    rpc.set_data({"rank": playerRank["rank"], "rank_name": colors.escape_ansi(NUMBERTORANKS[playerRank["rank"]]) + " | " + str(playerRank["rr"]) + "rr"})

                            # rankStatus = playerRank[1]
                            #useless code since rate limit is handled in the requestsV
                            # while not rankStatus:
                            #     print("You have been rate limited, 😞 waiting 10 seconds!")
                            #     time.sleep(10)
                            #     playerRank = rank.get_rank(player["Subject"], seasonID)
                            #     rankStatus = playerRank[1]
                            # playerRank = playerRank["rank"]

                            ppstats = pstats.get_stats(player["Subject"])
                            hs = ppstats["hs"]
                            kd = ppstats["kd"]

                            player_level = player["PlayerIdentity"].get("AccountLevel")
                            PLcolor = colors.level_to_color(player_level)

                            # AGENT
                            agent = ""

                            # NAME
                            name = color(names[player["Subject"]], fore=(76, 151, 237))

                            # RANK
                            rankName = NUMBERTORANKS[playerRank["rank"]]
                            if cfg.get_feature_flag("aggregate_rank_rr") and cfg.table.get("rr"):
                                rankName += f" ({playerRank['rr']})"

                            # RANK RATING
                            rr = playerRank["rr"]

                            #short peak rank string
                            has_letter = any(c.isalpha() for c in str(playerRank['peakrankep']))
                            peakRankAct = f" ({playerRank['peakrankep']}a{playerRank['peakrankact']})" if has_letter else f" (e{playerRank['peakrankep']}a{playerRank['peakrankact']})"
                            if not cfg.get_feature_flag("peak_rank_act"):
                                peakRankAct = ""

                            # PEAK RANK
                            peakRank = NUMBERTORANKS[playerRank["peakrank"]] + peakRankAct

                            # PREVIOUS RANK
                            previousRank = NUMBERTORANKS[previousPlayerRank["rank"]]

                            # LEADERBOARD
                            leaderboard = playerRank["leaderboard"]

                            hs = colors.get_hs_gradient(hs)
                            wr = colors.get_wr_gradient(playerRank["wr"]) + f" ({playerRank['numberofgames']})"

                            if(int(leaderboard)>0):
                                is_leaderboard_needed = True

                            # LEVEL
                            level = PLcolor

                            table.add_row_table([party_icon,
                                                agent,
                                                name,
                                                "",
                                                rankName,
                                                rr,
                                                peakRank,
                                                previousRank,
                                                leaderboard,
                                                hs,
                                                wr,
                                                kd,
                                                level
                                                ])
                            
                            heartbeat_data["players"][player["Subject"]] = {
                                "name": names[player["Subject"]],
                                "rank": playerRank["rank"],
                                "peakRank": playerRank["peakrank"],
                                "peakRankAct": peakRankAct,
                                "level": player_level,
                                "rr": rr,
                                "kd": ppstats["kd"],
                                "headshotPercentage": ppstats["hs"],
                                "winPercentage": f"{playerRank['wr']} ({playerRank['numberofgames']})",
                            }

                            # bar()
                    seen.append(player["Subject"])
            if (title := game_state_dict.get(game_state)) is None:
                # program_exit(1)
                time.sleep(9)
            if server != "":
                table.set_title(f"VALORANT status: {title} {colr('- ' + server, fore=(200, 200, 200))}")
            else:
                table.set_title(f"VALORANT status: {title}")
            server = ""
            if title is not None:
                if cfg.get_feature_flag("auto_hide_leaderboard") and (not is_leaderboard_needed):
                    table.set_runtime_col_flag('Pos.', False)

                if game_state == "MENUS":
                    table.set_runtime_col_flag('Party', False)
                    table.set_runtime_col_flag('Agent', False)
                    table.set_runtime_col_flag('Skin', False)

                if game_state == "INGAME":
                    if isRange:
                        table.set_runtime_col_flag('Party', False)
                        table.set_runtime_col_flag('Agent', False)

                # We don't to show the RR column if the "aggregate_rank_rr" feature flag is True.
                table.set_runtime_col_flag('RR', cfg.table.get("rr") and not cfg.get_feature_flag("aggregate_rank_rr"))

                table.set_caption(f"VALORANT rank yoinker v{version}")
                Server.send_payload("heartbeat",heartbeat_data)
                table.display()
                firstPrint = False

                # print(f"VALORANT rank yoinker v{version}")
                if cfg.get_feature_flag("last_played"):
                    if len(already_played_with) > 0:
                        print("\n")
                        for played in already_played_with:
                            print(f"Already played with {played['name']} (last {played['agent']}) {stats.convert_time(played['time_diff'])} ago. (Total played {played['times']} times)")
                already_played_with = []
        if cfg.cooldown == 0:
            input("Press enter to fetch again...")
        else:
            # time.sleep(cfg.cooldown)
            pass
except KeyboardInterrupt:
    #lame implementation of fast ctrl+c exit
    os._exit(0)
except:
    log(traceback.format_exc())
    print(color(
        "The program has encountered an error. If the problem persists, please reach support"
        f" with the logs found in {os.getcwd()}\\logs", fore=(255, 0, 0)))
    input("press enter to exit...\n")
    os._exit(1)
