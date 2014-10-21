'''
John Choiniere's Baseball Simulator

---See LICENSE.txt for licensing/use information.
------Licensed under the Apache 2.0 license.

---Based on odds ratio calculations as explained by Tom Tango (aka Tangotiger)
here: http://www.insidethebook.com/ee/index.php/site/comments/the_odds_ratio_method/

---Last update: 20 October 2014

---NEXT THING To do: error handling on inputs
------Right now, the program crashes if the user
------inputs something incorrectly (typos,
------uncapitalized names, nonexistent players, etc).
---------UPDATE: now have error handling on names, not yet on year

---To do: Clean up results
------Currently just printing dictionaries. Would be
------better to format printing, and give user option
------to save results to CSV file. Also need to add
------result ratio calculation (i.e., AVG, OBP)

---To do: Improve baserunning


CURRENT INSTRUCTIONS (Windows, anything else you're on your own):
0. Make sure there's a subdirectory called "data" in the folder where
you have this file, filled with files with names formatted "XXXXp.csv",
"XXXXb.csv", and "XXXXmlb.csv". The XXXX should be years from 1974-2013.
These are where the program draws its stats from.

1. Open a command prompt window in the folder where this file is.
2. Run "python bb_frame.py"
3. When prompted, enter the year from which to draw stats for the sim.
4. As prompted, enter home and away batting lineups, with a single pitcher
for each team. It's up to you whether the pitcher bats or not, but he would
need to be entered as both a batter and pitcher if so. PLEASE NOTE that any
typos, non-capitalization, or other errors (including entering someone who
didn't play in a given year) will crash the whole thing.
5. Enter the number of games you wish to simulate.
6. See your results!

KNOWN ISSUE:
The MySQL csv outputs are a little funky if an event didn't happen in a given
year. Nulls became backslash-capital-N. I assume this messes with the program,
but it can be avoided if you stick to players who played a lot (and starting
pitchers only).

KNOWN ISSUE:
I haven't checked, but I'm pretty sure batted ball info is a recent thing in
retrosheet, which is where my stats come from. Best stick to recent years if 
you try this out.
'''

import random
import time
import mysql.connector
from mysql.connector import errorcode
from collections import Counter
import csv

#Function for testing MySQL connection
#DEPRECATED as of converting to CSV input, can be deleted eventually
def test_db():
	try:
		cnx = mysql.connector.connect(user='root',password='Louis and Marie',database='baseball')
	except mysql.connector.Error as err:
		if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
			print("Something is wrong with your user name or password")
		elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print("Database does not exists")
		else:
			print(err)
	else:
		cnx.close()

#Function for importing seasonal data from CSVs.
#For batters, pitchers, and league (I'd like to write league a little different in the future)
#it loads the associated file with the year it's given, and creates either a dictionary of
#dictionaries in the case of batters/pitchers or just a plain old dictionary for MLB.
#The dictionaries all_batters and all_pitchers use player name (capitalized) as the keys
#and dictionaries of the needed binomial ratios in the format (stat_name(str) : float) as the values
def season_import(year):
	global all_batters
	global all_pitchers
	global mlb
	all_batters = {}
	all_pitchers = {}
	mlb = {}
	with open("data/"+year+"b.csv") as f_1:
		input_file = csv.DictReader(f_1)
		for row in input_file:
			row_name = str(row['name'])
			all_batters[row_name] = row
	with open("data/"+year+"p.csv") as f_2:
		input_file = csv.DictReader(f_2)
		for row in input_file:
			row_name = str(row['name'])
			all_pitchers[row_name] = row
	with open("data/"+year+"mlb.csv") as f_3:
		input_file = csv.DictReader(f_3)
		for row in input_file:
			mlb = row
	#Error-diagnosing:
	#print(all_batters)
	#print(all_pitchers)
	#print(mlb)
		
#Function for finding retrosheet_ID for db lookup from typed input
#DEPRECATED as of converting to CSV input, can be deleted eventually
def get_retroid(player):
	cnx = mysql.connector.connect(user='root',password='Louis and Marie',database='baseball')
	cursor = cnx.cursor()
	query = ("SELECT retroID FROM master_new_retro_ids WHERE (nameFirst = %s and nameLast = %s)")
	firstname,lastname = player.split()
	cursor.execute(query,(firstname,lastname))
	retroid = cursor.fetchone()
	return retroid[0]

#Function for getting relevant stats based on get_retroid() output from db
#DEPRECATED as of converting to CSV input, can be deleted eventually
def get_hitting_stats(player):
	player = get_retroid(player)
	cnx = mysql.connector.connect(user='root',password='Louis and Marie',database='baseball')
	cursor = cnx.cursor(dictionary=True)
	query = ("select resp_bat_ID AS retroid,sum(if(event_cd=16,1,0))/count(*) AS hbp_pct,sum(if(event_cd<>16,1,0))/count(*) AS nonhbp_pct,sum(if(event_cd=3 OR event_cd=14 OR event_cd=15,1,0))/sum(if(event_cd<>16,1,0)) AS noncontact_per_nonhbp_pct,sum(if(event_cd<>3 AND event_cd<>14 AND event_cd<>15,1,0))/sum(if(event_cd<>16,1,0)) AS contact_per_nonhbp_pct,sum(if(event_cd=3,1,0))/sum(if(event_cd=3 or event_cd=14,1,0)) AS k_per_noncontact_pct,sum(if(event_cd=14,1,0))/sum(if(event_cd=3 or event_cd=14,1,0)) AS bb_per_noncontact_pct,sum(if(battedball_cd='G',1,0))/sum(if(battedball_cd<>'',1,0)) AS onground_per_contact_pct,sum(if(battedball_cd<>'G' and battedball_cd<>'',1,0))/sum(if(battedball_cd<>'',1,0)) AS inair_per_contact_pct,sum(if(battedball_cd='P',1,0))/sum(if(battedball_cd<>'' and battedball_cd<>'G',1,0)) AS iffb_per_inair_pct,sum(if(battedball_cd='L' or battedball_cd='F',1,0))/sum(if(battedball_cd<>'' and battedball_cd<>'G',1,0)) AS noniffb_per_inair_pct,sum(if(event_cd=23 AND (battedball_cd='F' OR battedball_cd='L'),1,0))/sum(if(battedball_cd='F' or battedball_cd='L',1,0)) AS hr_per_noniffb_pct,sum(if(event_cd<>23 AND (battedball_cd='F' OR battedball_cd='L'),1,0))/sum(if(battedball_cd='F' or battedball_cd='L',1,0)) AS nonhr_per_noniffb_pct,sum(if(battedball_cd='L' AND event_cd<>23,1,0))/sum(if(event_cd<>23 AND (battedball_cd='L' OR battedball_cd='F'),1,0)) AS ld_per_nonhr_pct,sum(if(battedball_cd='F' AND event_cd<>23,1,0))/sum(if(event_cd<>23 AND (battedball_cd='L' OR battedball_cd='F'),1,0)) AS fb_per_nonhr_pct,sum(if(event_cd<20 AND battedball_cd='L',1,0))/sum(if(battedball_cd='L' AND event_cd<>23,1,0)) AS out_per_ld_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0))/sum(if(battedball_cd='L' AND event_cd<>23,1,0)) AS nonout_per_ld_pct,sum(if(event_cd=20 AND battedball_cd='L',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0)) AS single_per_nonoutl_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='L',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0)) AS xb_per_nonoutl_pct,sum(if(event_cd<20 AND battedball_cd='F',1,0))/sum(if(battedball_cd='F' AND event_cd<>23,1,0)) AS out_per_fb_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='F',1,0))/sum(if(battedball_cd='F' AND event_cd<>23,1,0)) AS nonout_per_fb_pct,sum(if(event_cd=20 AND battedball_cd='F',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='f',1,0)) AS single_per_nonoutf_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='F',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='F',1,0)) AS xb_per_nonoutf_pct,sum(if(event_cd<20 AND battedball_cd='G',1,0))/sum(if(battedball_cd='G',1,0)) AS out_per_onground_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0))/sum(if(battedball_cd='G',1,0)) AS nonout_per_onground_pct,sum(if(event_cd=20 AND battedball_cd='G',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0)) AS single_per_nonoutg_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='G',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0)) AS xb_per_nonoutg_pct from events_regseason WHERE (year_ID = 2013 AND bat_event_fl='T' AND bunt_fl<>'T' AND foul_fl<>'T' AND event_cd<>15 AND resp_bat_ID = '%s')")
	cursor.execute(query % player)
	stat_line = cursor.fetchall()
	#print(stat_line)
	return stat_line

#Function for getting relevant stats based on get_retroid() output from db
#DEPRECATED as of converting to CSV input, can be deleted eventually
def get_pitching_stats(player):
	player = get_retroid(player)
	cnx = mysql.connector.connect(user='root',password='Louis and Marie',database='baseball')
	cursor = cnx.cursor(dictionary=True)
	query = ("select res_pit_ID AS retroid,sum(if(event_cd=16,1,0))/count(*) AS hbp_pct,sum(if(event_cd<>16,1,0))/count(*) AS nonhbp_pct,sum(if(event_cd=3 OR event_cd=14 OR event_cd=15,1,0))/sum(if(event_cd<>16,1,0)) AS noncontact_per_nonhbp_pct,sum(if(event_cd<>3 AND event_cd<>14 AND event_cd<>15,1,0))/sum(if(event_cd<>16,1,0)) AS contact_per_nonhbp_pct,sum(if(event_cd=3,1,0))/sum(if(event_cd=3 or event_cd=14,1,0)) AS k_per_noncontact_pct,sum(if(event_cd=14,1,0))/sum(if(event_cd=3 or event_cd=14,1,0)) AS bb_per_noncontact_pct,sum(if(battedball_cd='G',1,0))/sum(if(battedball_cd<>'',1,0)) AS onground_per_contact_pct,sum(if(battedball_cd<>'G' and battedball_cd<>'',1,0))/sum(if(battedball_cd<>'',1,0)) AS inair_per_contact_pct,sum(if(battedball_cd='P',1,0))/sum(if(battedball_cd<>'' and battedball_cd<>'G',1,0)) AS iffb_per_inair_pct,sum(if(battedball_cd='L' or battedball_cd='F',1,0))/sum(if(battedball_cd<>'' and battedball_cd<>'G',1,0)) AS noniffb_per_inair_pct,sum(if(event_cd=23 AND (battedball_cd='F' OR battedball_cd='L'),1,0))/sum(if(battedball_cd='F' or battedball_cd='L',1,0)) AS hr_per_noniffb_pct,sum(if(event_cd<>23 AND (battedball_cd='F' OR battedball_cd='L'),1,0))/sum(if(battedball_cd='F' or battedball_cd='L',1,0)) AS nonhr_per_noniffb_pct,sum(if(battedball_cd='L' AND event_cd<>23,1,0))/sum(if(event_cd<>23 AND (battedball_cd='L' OR battedball_cd='F'),1,0)) AS ld_per_nonhr_pct,sum(if(battedball_cd='F' AND event_cd<>23,1,0))/sum(if(event_cd<>23 AND (battedball_cd='L' OR battedball_cd='F'),1,0)) AS fb_per_nonhr_pct,sum(if(event_cd<20 AND battedball_cd='L',1,0))/sum(if(battedball_cd='L' AND event_cd<>23,1,0)) AS out_per_ld_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0))/sum(if(battedball_cd='L' AND event_cd<>23,1,0)) AS nonout_per_ld_pct,sum(if(event_cd=20 AND battedball_cd='L',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0)) AS single_per_nonoutl_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='L',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='L',1,0)) AS xb_per_nonoutl_pct,sum(if(event_cd<20 AND battedball_cd='F',1,0))/sum(if(battedball_cd='F' AND event_cd<>23,1,0)) AS out_per_fb_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='F',1,0))/sum(if(battedball_cd='F' AND event_cd<>23,1,0)) AS nonout_per_fb_pct,sum(if(event_cd=20 AND battedball_cd='F',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='f',1,0)) AS single_per_nonoutf_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='F',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='F',1,0)) AS xb_per_nonoutf_pct,sum(if(event_cd<20 AND battedball_cd='G',1,0))/sum(if(battedball_cd='G',1,0)) AS out_per_onground_pct,sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0))/sum(if(battedball_cd='G',1,0)) AS nonout_per_onground_pct,sum(if(event_cd=20 AND battedball_cd='G',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0)) AS single_per_nonoutg_pct,sum(if((event_cd=21 or event_cd=22) AND battedball_cd='G',1,0))/sum(if(event_cd>19 AND event_cd<23 AND battedball_cd='G',1,0)) AS xb_per_nonoutg_pct from events_regseason WHERE (year_ID = 2013 AND bat_event_fl='T' AND bunt_fl<>'T' AND foul_fl<>'T' AND event_cd<>15 AND res_pit_ID = '%s')")
	cursor.execute(query % player)
	stat_line = cursor.fetchall()
	#print(stat_line)
	return stat_line

#Function for assembling team starting lineups
def build_rosters():
	#Establishes dictionaries of player names and ratios for each team
	global home_team_lineup
	global home_team_stats
	global home_team_pitchers
	global home_team_pstats
	global away_team_lineup
	global away_team_stats
	global away_team_pitchers
	global away_team_pstats
	home_team_lineup={}
	home_team_stats={}
	home_team_pitchers={}
	home_team_pstats={}
	away_team_lineup={}
	away_team_stats={}
	away_team_pitchers={}
	away_team_pstats={}
	#Counters, essentially, to track the number of players per team. E.g., hb is "home batters"
	hb = 0
	hp = 0
	ab = 0
	ap = 0
	year = input("Data year: ")
	season_import(year)
	#No subbing mech. yet, so just goes 1-9 for batters (lineup order)
	while hb < 9:
		try:
			player = input(str(hb+1)+"th Player (Home): ")
			firstname, lastname = player.split()
			player = firstname.capitalize()+" "+lastname.capitalize()
			home_team_lineup[hb] = player
			home_team_stats[player] = all_batters[player]
			hb += 1
		except ValueError:
			print("ERROR: Invalid Name Construction, try again")
		except KeyError:
			print("ERROR: Player Not Found, try again")
	while hp < 1:
		try:
			pitcher = input(str(hp+1)+"st Pitcher (Home): ")
			firstname, lastname = pitcher.split()
			pitcher = firstname.capitalize()+" "+lastname.capitalize()
			home_team_pitchers[hp] = pitcher
			home_team_pstats[pitcher] = all_pitchers[pitcher]
			hp += 1
		except ValueError:
			print("ERROR: Invalid Name Construction, try again")
		except KeyError:
			print("ERROR: Player Not Found, try again")
	while ab < 9:
		try:
			player = input(str(ab+1)+"th Player (Away): ")
			firstname, lastname = player.split()
			player = firstname.capitalize()+" "+lastname.capitalize()
			away_team_lineup[ab] = player
			away_team_stats[player] = all_batters[player]
			ab += 1
		except ValueError:
			print("ERROR: Invalid Name Construction, try again")
		except KeyError:
			print("ERROR: Player Not Found, try again")
	while ap < 1:
		try:
			pitcher = input(str(ap+1)+"st Pitcher (Away): ")
			firstname, lastname = pitcher.split()
			pitcher = firstname.capitalize()+" "+lastname.capitalize()
			away_team_pitchers[ap] = pitcher
			away_team_pstats[pitcher] = all_pitchers[pitcher]
			ap += 1
		except ValueError:
			print("ERROR: Invalid Name Construction, try again")
		except KeyError:
			print("ERROR: Player Not Found, try again")

#Function for setting all odds to values for specific players and leagues
def set_odds(batter, pitcher):
	global b_hbp_pct
	global b_nonhbp_pct
	global b_contact_per_nonhbp_pct
	global b_noncontact_per_nonhbp_pct
	global b_k_per_noncontact_pct
	global b_bb_per_noncontact_pct
	global b_inair_per_contact_pct
	global b_onground_per_contact_pct
	global b_out_per_onground_pct
	global b_nonout_per_onground_pct
	global b_single_per_nonoutg_pct
	global b_xb_per_nonoutg_pct
	global b_iffb_per_inair_pct
	global b_noniffb_per_inair_pct
	global b_hr_per_noniffb_pct
	global b_nonhr_per_noniffb_pct
	global b_ld_per_nonhr_pct
	global b_fb_per_nonhr_pct
	global b_out_per_ld_pct
	global b_nonout_per_ld_pct
	global b_single_per_nonoutl_pct
	global b_xb_per_nonoutl_pct
	global b_out_per_fb_pct
	global b_nonout_per_fb_pct
	global b_single_per_nonoutf_pct
	global b_xb_per_nonoutf_pct
	global p_hbp_pct
	global p_nonhbp_pct_pct
	global p_contact_per_nonhbp_pct
	global p_noncontact_per_nonhbp_pct
	global p_k_per_noncontact_pct
	global p_bb_per_noncontact_pct
	global p_inair_per_contact_pct
	global p_onground_per_contact_pct
	global p_out_per_onground_pct
	global p_nonout_per_onground_pct
	global p_single_per_nonoutg_pct
	global p_xb_per_nonoutg_pct
	global p_iffb_per_inair_pct
	global p_noniffb_per_inair_pct
	global p_hr_per_noniffb_pct
	global p_nonhr_per_noniffb_pct
	global p_ld_per_nonhr_pct
	global p_fb_per_nonhr_pct
	global p_out_per_ld_pct
	global p_nonout_per_ld_pct
	global p_single_per_nonoutl_pct
	global p_xb_per_nonoutl_pct
	global p_out_per_fb_pct
	global p_nonout_per_fb_pct
	global p_single_per_nonoutf_pct
	global p_xb_per_nonoutf_pct
	global l_hbp_pct
	global l_nonhbp_pct
	global l_contact_per_nonhbp_pct
	global l_noncontact_per_nonhbp_pct
	global l_k_per_noncontact_pct
	global l_bb_per_noncontact_pct
	global l_inair_per_contact_pct
	global l_onground_per_contact_pct
	global l_out_per_onground_pct
	global l_nonout_per_onground_pct
	global l_single_per_nonoutg_pct
	global l_xb_per_nonoutg_pct
	global l_iffb_per_inair_pct
	global l_noniffb_per_inair_pct
	global l_hr_per_noniffb_pct
	global l_nonhr_per_noniffb_pct
	global l_ld_per_nonhr_pct
	global l_fb_per_nonhr_pct
	global l_out_per_ld_pct
	global l_nonout_per_ld_pct
	global l_single_per_nonoutl_pct
	global l_xb_per_nonoutl_pct
	global l_out_per_fb_pct
	global l_nonout_per_fb_pct
	global l_single_per_nonoutf_pct
	global l_xb_per_nonoutf_pct
	b_hbp_pct=float(batter["hbp_pct"])
	b_nonhbp_pct=float(batter["nonhbp_pct"])
	b_contact_per_nonhbp_pct=float(batter["contact_per_nonhbp_pct"])
	b_noncontact_per_nonhbp_pct=float(batter["noncontact_per_nonhbp_pct"])
	b_k_per_noncontact_pct=float(batter["K_per_noncontact_pct"])
	b_bb_per_noncontact_pct=float(batter["bb_per_noncontact_pct"])
	b_inair_per_contact_pct=float(batter["inair_per_contact_pct"])
	b_onground_per_contact_pct=float(batter["onground_per_contact_pct"])
	b_out_per_onground_pct=float(batter["out_per_onground_pct"])
	b_nonout_per_onground_pct=float(batter["nonout_per_onground_pct"])
	b_single_per_nonoutg_pct=float(batter["single_per_nonoutg_pct"])
	b_xb_per_nonoutg_pct=float(batter["xb_per_nonoutg_pct"])
	b_iffb_per_inair_pct=float(batter["iffb_per_inair_pct"])
	b_noniffb_per_inair_pct=float(batter["noniffb_per_inair_pct"])
	b_hr_per_noniffb_pct=float(batter["hr_per_noniffb_pct"])
	b_nonhr_per_noniffb_pct=float(batter["nonhr_per_noniffb_pct"])
	b_ld_per_nonhr_pct=float(batter["ld_per_nonhr_pct"])
	b_fb_per_nonhr_pct=float(batter["fb_per_nonhr_pct"])
	b_out_per_ld_pct=float(batter["out_per_ld_pct"])
	b_nonout_per_ld_pct=float(batter["nonout_per_ld_pct"])
	b_single_per_nonoutl_pct=float(batter["single_per_nonoutl_pct"])
	b_xb_per_nonoutl_pct=float(batter["xb_per_nonoutl_pct"])
	b_out_per_fb_pct=float(batter["out_per_fb_pct"])
	b_nonout_per_fb_pct=float(batter["nonout_per_fb_pct"])
	b_single_per_nonoutf_pct=float(batter["single_per_nonoutf_pct"])
	b_xb_per_nonoutf_pct=float(batter["xb_per_nonoutf_pct"])
	p_hbp_pct=float(pitcher["hbp_pct"])
	p_nonhbp_pct=float(pitcher["nonhbp_pct"])
	p_contact_per_nonhbp_pct=float(pitcher["contact_per_nonhbp_pct"])
	p_noncontact_per_nonhbp_pct=float(pitcher["noncontact_per_nonhbp_pct"])
	p_k_per_noncontact_pct=float(pitcher["K_per_noncontact_pct"])
	p_bb_per_noncontact_pct=float(pitcher["bb_per_noncontact_pct"])
	p_inair_per_contact_pct=float(pitcher["inair_per_contact_pct"])
	p_onground_per_contact_pct=float(pitcher["onground_per_contact_pct"])
	p_out_per_onground_pct=float(pitcher["out_per_onground_pct"])
	p_nonout_per_onground_pct=float(pitcher["nonout_per_onground_pct"])
	p_single_per_nonoutg_pct=float(pitcher["single_per_nonoutg_pct"])
	p_xb_per_nonoutg_pct=float(pitcher["xb_per_nonoutg_pct"])
	p_iffb_per_inair_pct=float(pitcher["iffb_per_inair_pct"])
	p_noniffb_per_inair_pct=float(pitcher["noniffb_per_inair_pct"])
	p_hr_per_noniffb_pct=float(pitcher["hr_per_noniffb_pct"])
	p_nonhr_per_noniffb_pct=float(pitcher["nonhr_per_noniffb_pct"])
	p_ld_per_nonhr_pct=float(pitcher["ld_per_nonhr_pct"])
	p_fb_per_nonhr_pct=float(pitcher["fb_per_nonhr_pct"])
	p_out_per_ld_pct=float(pitcher["out_per_ld_pct"])
	p_nonout_per_ld_pct=float(pitcher["nonout_per_ld_pct"])
	p_single_per_nonoutl_pct=float(pitcher["single_per_nonoutl_pct"])
	p_xb_per_nonoutl_pct=float(pitcher["xb_per_nonoutl_pct"])
	p_out_per_fb_pct=float(pitcher["out_per_fb_pct"])
	p_nonout_per_fb_pct=float(pitcher["nonout_per_fb_pct"])
	p_single_per_nonoutf_pct=float(pitcher["single_per_nonoutf_pct"])
	p_xb_per_nonoutf_pct=float(pitcher["xb_per_nonoutf_pct"])
	l_hbp_pct=float(mlb["hbp_pct"])
	l_nonhbp_pct=float(mlb["nonhbp_pct"])
	l_contact_per_nonhbp_pct=float(mlb["contact_per_nonhbp_pct"])
	l_noncontact_per_nonhbp_pct=float(mlb["noncontact_per_nonhbp_pct"])
	l_k_per_noncontact_pct=float(mlb["K_per_noncontact_pct"])
	l_bb_per_noncontact_pct=float(mlb["bb_per_noncontact_pct"])
	l_inair_per_contact_pct=float(mlb["inair_per_contact_pct"])
	l_onground_per_contact_pct=float(mlb["onground_per_contact_pct"])
	l_out_per_onground_pct=float(mlb["out_per_onground_pct"])
	l_nonout_per_onground_pct=float(mlb["nonout_per_onground_pct"])
	l_single_per_nonoutg_pct=float(mlb["single_per_nonoutg_pct"])
	l_xb_per_nonoutg_pct=float(mlb["xb_per_nonoutg_pct"])
	l_iffb_per_inair_pct=float(mlb["iffb_per_inair_pct"])
	l_noniffb_per_inair_pct=float(mlb["noniffb_per_inair_pct"])
	l_hr_per_noniffb_pct=float(mlb["hr_per_noniffb_pct"])
	l_nonhr_per_noniffb_pct=float(mlb["nonhr_per_noniffb_pct"])
	l_ld_per_nonhr_pct=float(mlb["ld_per_nonhr_pct"])
	l_fb_per_nonhr_pct=float(mlb["fb_per_nonhr_pct"])
	l_out_per_ld_pct=float(mlb["out_per_ld_pct"])
	l_nonout_per_ld_pct=float(mlb["nonout_per_ld_pct"])
	l_single_per_nonoutl_pct=float(mlb["single_per_nonoutl_pct"])
	l_xb_per_nonoutl_pct=float(mlb["xb_per_nonoutl_pct"])
	l_out_per_fb_pct=float(mlb["out_per_fb_pct"])
	l_nonout_per_fb_pct=float(mlb["nonout_per_fb_pct"])
	l_single_per_nonoutf_pct=float(mlb["single_per_nonoutf_pct"])
	l_xb_per_nonoutf_pct=float(mlb["xb_per_nonoutf_pct"])


#Function for combining odds
#The first function listed in each pair is taken as the "controlling" ratio, if you will;
#the odds ratio concept requires binary outcomes and can give you the odds of one side of
#the outcome only. According to Tango there's not a "right" order for this, and ideally we
#(or someone) should work out some sort of study to try to establish it empirically.
def odds_combo():
	comb_hbp_pct = ((b_hbp_pct/(1-b_hbp_pct))*(p_hbp_pct/(1-p_hbp_pct))/(l_hbp_pct/(1-l_hbp_pct)))/(1+((b_hbp_pct/(1-b_hbp_pct))*(p_hbp_pct/(1-p_hbp_pct))/(l_hbp_pct/(1-l_hbp_pct))))
	comb_nonhbp_pct = 1-comb_hbp_pct
	
	comb_contact_per_nonhbp_pct = ((b_contact_per_nonhbp_pct/(1-b_contact_per_nonhbp_pct))*(p_contact_per_nonhbp_pct/(1-p_contact_per_nonhbp_pct))/(l_contact_per_nonhbp_pct/(1-l_contact_per_nonhbp_pct)))/(1+((b_contact_per_nonhbp_pct/(1-b_contact_per_nonhbp_pct))*(p_contact_per_nonhbp_pct/(1-p_contact_per_nonhbp_pct))/(l_contact_per_nonhbp_pct/(1-l_contact_per_nonhbp_pct))))
	comb_noncontact_per_nonhbp_pct = 1-comb_contact_per_nonhbp_pct
	
	comb_k_per_noncontact_pct = ((b_k_per_noncontact_pct/(1-b_k_per_noncontact_pct))*(p_k_per_noncontact_pct/(1-p_k_per_noncontact_pct))/(l_k_per_noncontact_pct/(1-l_k_per_noncontact_pct)))/(1+((b_k_per_noncontact_pct/(1-b_k_per_noncontact_pct))*(p_k_per_noncontact_pct/(1-p_k_per_noncontact_pct))/(l_k_per_noncontact_pct/(1-l_k_per_noncontact_pct))))
	comb_bb_per_noncontact_pct = 1-comb_k_per_noncontact_pct
	
	comb_inair_per_contact_pct = ((b_inair_per_contact_pct/(1-b_inair_per_contact_pct))*(p_inair_per_contact_pct/(1-p_inair_per_contact_pct))/(l_inair_per_contact_pct/(1-l_inair_per_contact_pct)))/(1+((b_inair_per_contact_pct/(1-b_inair_per_contact_pct))*(p_inair_per_contact_pct/(1-p_inair_per_contact_pct))/(l_inair_per_contact_pct/(1-l_inair_per_contact_pct))))
	comb_onground_per_contact_pct = 1-comb_inair_per_contact_pct
	
	comb_out_per_onground_pct = ((b_out_per_onground_pct/(1-b_out_per_onground_pct))*(p_out_per_onground_pct/(1-p_out_per_onground_pct))/(l_out_per_onground_pct/(1-l_out_per_onground_pct)))/(1+((b_out_per_onground_pct/(1-b_out_per_onground_pct))*(p_out_per_onground_pct/(1-p_out_per_onground_pct))/(l_out_per_onground_pct/(1-l_out_per_onground_pct))))
	comb_nonout_per_onground_pct = 1-comb_out_per_onground_pct
	
	comb_single_per_nonoutg_pct = ((b_single_per_nonoutg_pct/(1-b_single_per_nonoutg_pct))*(p_single_per_nonoutg_pct/(1-p_single_per_nonoutg_pct))/(l_single_per_nonoutg_pct/(1-l_single_per_nonoutg_pct)))/(1+((b_single_per_nonoutg_pct/(1-b_single_per_nonoutg_pct))*(p_single_per_nonoutg_pct/(1-p_single_per_nonoutg_pct))/(l_single_per_nonoutg_pct/(1-l_single_per_nonoutg_pct))))
	comb_xb_per_nonoutg_pct = 1-comb_single_per_nonoutg_pct
	
	comb_single_per_nonoutl_pct = ((b_single_per_nonoutl_pct/(1-b_single_per_nonoutl_pct))*(p_single_per_nonoutl_pct/(1-p_single_per_nonoutl_pct))/(l_single_per_nonoutl_pct/(1-l_single_per_nonoutl_pct)))/(1+((b_single_per_nonoutl_pct/(1-b_single_per_nonoutl_pct))*(p_single_per_nonoutl_pct/(1-p_single_per_nonoutl_pct))/(l_single_per_nonoutl_pct/(1-l_single_per_nonoutl_pct))))
	comb_xb_per_nonoutl_pct = 1-comb_single_per_nonoutl_pct
	
	comb_single_per_nonoutf_pct = ((b_single_per_nonoutf_pct/(1-b_single_per_nonoutf_pct))*(p_single_per_nonoutf_pct/(1-p_single_per_nonoutf_pct))/(l_single_per_nonoutf_pct/(1-l_single_per_nonoutf_pct)))/(1+((b_single_per_nonoutf_pct/(1-b_single_per_nonoutf_pct))*(p_single_per_nonoutf_pct/(1-p_single_per_nonoutf_pct))/(l_single_per_nonoutf_pct/(1-l_single_per_nonoutf_pct))))
	comb_xb_per_nonoutf_pct = 1-comb_single_per_nonoutf_pct
	
	comb_iffb_per_inair_pct = ((b_iffb_per_inair_pct/(1-b_iffb_per_inair_pct))*(p_iffb_per_inair_pct/(1-p_iffb_per_inair_pct))/(l_iffb_per_inair_pct/(1-l_iffb_per_inair_pct)))/(1+((b_iffb_per_inair_pct/(1-b_iffb_per_inair_pct))*(p_iffb_per_inair_pct/(1-p_iffb_per_inair_pct))/(l_iffb_per_inair_pct/(1-l_iffb_per_inair_pct))))
	comb_noniffb_per_inair_pct = 1-comb_iffb_per_inair_pct
	
	comb_hr_per_noniffb_pct = ((b_hr_per_noniffb_pct/(1-b_hr_per_noniffb_pct))*(p_hr_per_noniffb_pct/(1-p_hr_per_noniffb_pct))/(l_hr_per_noniffb_pct/(1-l_hr_per_noniffb_pct)))/(1+((b_hr_per_noniffb_pct/(1-b_hr_per_noniffb_pct))*(p_hr_per_noniffb_pct/(1-p_hr_per_noniffb_pct))/(l_hr_per_noniffb_pct/(1-l_hr_per_noniffb_pct))))
	comb_nonhr_per_noniffb_pct = 1-comb_hr_per_noniffb_pct
	
	comb_ld_per_nonhr_pct = ((b_ld_per_nonhr_pct/(1-b_ld_per_nonhr_pct))*(p_ld_per_nonhr_pct/(1-p_ld_per_nonhr_pct))/(l_ld_per_nonhr_pct/(1-l_ld_per_nonhr_pct)))/(1+((b_ld_per_nonhr_pct/(1-b_ld_per_nonhr_pct))*(p_ld_per_nonhr_pct/(1-p_ld_per_nonhr_pct))/(l_ld_per_nonhr_pct/(1-l_ld_per_nonhr_pct))))
	comb_fb_per_nonhr_pct = 1-comb_ld_per_nonhr_pct
	
	comb_out_per_ld_pct = ((b_out_per_ld_pct/(1-b_out_per_ld_pct))*(p_out_per_ld_pct/(1-p_out_per_ld_pct))/(l_out_per_ld_pct/(1-l_out_per_ld_pct)))/(1+((b_out_per_ld_pct/(1-b_out_per_ld_pct))*(p_out_per_ld_pct/(1-p_out_per_ld_pct))/(l_out_per_ld_pct/(1-l_out_per_ld_pct))))
	comb_nonout_per_ld_pct = 1-comb_out_per_ld_pct
	
	comb_out_per_fb_pct = ((b_out_per_fb_pct/(1-b_out_per_fb_pct))*(p_out_per_fb_pct/(1-p_out_per_fb_pct))/(l_out_per_fb_pct/(1-l_out_per_fb_pct)))/(1+((b_out_per_fb_pct/(1-b_out_per_fb_pct))*(p_out_per_fb_pct/(1-p_out_per_fb_pct))/(l_out_per_fb_pct/(1-l_out_per_fb_pct))))
	comb_nonout_per_fb_pct = 1-comb_out_per_fb_pct
	
	global hbp_pct
	global ld1b_pct
	global ldxb_pct
	global ldout_pct
	global fb1b_pct
	global fbxb_pct
	global fbout_pct
	global hr_pct
	global iffb_pct
	global gb1b_pct
	global gbxb_pct
	global gbout_pct
	global k_pct
	global bb_pct
	global checksum
	#The chained outcomes:
	hbp_pct = comb_hbp_pct
	k_pct = comb_k_per_noncontact_pct * comb_noncontact_per_nonhbp_pct * comb_nonhbp_pct
	bb_pct = comb_bb_per_noncontact_pct * comb_noncontact_per_nonhbp_pct * comb_nonhbp_pct
	hr_pct = comb_hr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	iffb_pct = comb_iffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	ld1b_pct = comb_single_per_nonoutl_pct * comb_nonout_per_ld_pct * comb_ld_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	ldxb_pct = comb_xb_per_nonoutl_pct * comb_nonout_per_ld_pct * comb_ld_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	ldout_pct = comb_out_per_ld_pct * comb_ld_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	fb1b_pct = comb_single_per_nonoutf_pct * comb_nonout_per_fb_pct * comb_fb_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	fbxb_pct = comb_xb_per_nonoutf_pct * comb_nonout_per_fb_pct * comb_fb_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	fbout_pct = comb_out_per_fb_pct * comb_fb_per_nonhr_pct * comb_nonhr_per_noniffb_pct * comb_noniffb_per_inair_pct * comb_inair_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	gb1b_pct = comb_single_per_nonoutg_pct * comb_nonout_per_onground_pct * comb_onground_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	gbxb_pct = comb_xb_per_nonoutg_pct * comb_nonout_per_onground_pct * comb_onground_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	gbout_pct = comb_out_per_onground_pct * comb_onground_per_contact_pct * comb_contact_per_nonhbp_pct * comb_nonhbp_pct
	checksum = hbp_pct + k_pct + bb_pct + hr_pct + iffb_pct + ld1b_pct + ldxb_pct + ldout_pct + gb1b_pct + gbxb_pct + gbout_pct + fb1b_pct + fbxb_pct + fbout_pct

#Function for creating a plate appearance outcome (obvious from the name, no?) - 
#Runs odds_combo(), generates a random number, and returns the outcome as a str
def PA_outcome():
	global hbp_pct
	global ld1b_pct
	global ldxb_pct
	global ldout_pct
	global fb1b_pct
	global fbxb_pct
	global fbout_pct
	global hr_pct
	global gb1b_pct
	global gbxb_pct
	global gbout_pct
	global k_pct
	global bb_pct
	global iffb_pct
	odds_combo()
	ldxb_pct = ldxb_pct + ld1b_pct
	fb1b_pct = fb1b_pct + ldxb_pct
	fbxb_pct = fbxb_pct + fb1b_pct
	gb1b_pct = gb1b_pct + fbxb_pct
	gbxb_pct = gbxb_pct + gb1b_pct
	hr_pct = hr_pct + gbxb_pct
	hbp_pct = hbp_pct + hr_pct
	bb_pct = bb_pct + hbp_pct
	iffb_pct = iffb_pct + bb_pct
	ldout_pct = ldout_pct + iffb_pct
	fbout_pct = fbout_pct + ldout_pct
	gbout_pct = gbout_pct + fbout_pct
	k_pct = k_pct + gbout_pct
	event = random.random()
	if event < ld1b_pct:
		return "ld1b"
	elif event < ldxb_pct:
		return "ldxb"
	elif event < fb1b_pct:
		return "fb1b"
	elif event < fbxb_pct:
		return "fbxb"
	elif event < gb1b_pct:
		return "gb1b"
	elif event < gbxb_pct:
		return "gbxb"
	elif event < hr_pct:
		return "hr"
	elif event < hbp_pct:
		return "hbp"
	elif event < bb_pct:
		return "bb"
	elif event < ldout_pct:
		return "ldout"
	elif event < fbout_pct:
		return "fbout"
	elif event < gbout_pct:
		return "gbout"
	elif event < k_pct:
		return "k"
	else:
		return "iffb"

#The central function.
#Function for simulating a game. 
def pbp():
	global outs
	global current_home_batter
	global current_away_batter
	global current_home_pitcher
	global current_away_pitcher
	global away_wins
	global home_wins
	#For each game, initializes at zero: outs, current place in 
	#home and away lineups (and pitchers), team runs, inning, and outs per inning.
	#Also sets batting team to away.
	outs = 0
	current_home_batter = 0
	current_away_batter = 0
	current_home_pitcher = 0
	current_away_pitcher = 0
	home_runs = 0
	away_runs = 0
	home_hits = 0
	away_hits = 0
	inning = 0
	inning_outs = 0
	away_team_at_bat = True
	while (outs < 51 or (outs >= 51 and home_runs == away_runs)):
		if away_team_at_bat == True:
			inning += 1
			inning_outs = 0
			first_base = ""
			second_base = ""
			third_base = ""
			while inning_outs<3:
				batter = away_team_lineup[current_away_batter]
				pitcher = home_team_pitchers[current_home_pitcher]
				set_odds(away_team_stats[batter],home_team_pstats[pitcher])
				event = PA_outcome()
				home_pitching_stats[pitcher]['TBF'] += 1
				if event == "iffb" or event == "gbout" or event == "fbout" or event == "ldout":
					#No advancement on outs for now
					outs += 1
					inning_outs += 1
					#note that hitting_stats or pitching_stats are record-keeping dictionaries,
					#as opposed to team_stats or team_pstats, which establish odds,
					#I will eventually rename things so they're not so similar.
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1	
					home_pitching_stats[pitcher]['Outs'] += 1
				elif event == "k":
					#No dropped 3rd strike yet
					outs += 1
					inning_outs += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['K'] += 1
					home_pitching_stats[pitcher]['Outs'] += 1
					home_pitching_stats[pitcher]['K'] += 1
				elif event == "hr":
					away_runs += 1
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['R'] += 1
					away_hitting_stats[batter]['HR'] += 1
					away_hitting_stats[batter]['H'] += 1
					away_hitting_stats[batter]['RBI'] += 1
					away_hitting_stats[batter]['XB'] += 1
					home_pitching_stats[pitcher]['HR'] += 1
					home_pitching_stats[pitcher]['RA'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					if first_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[first_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						first_base = ""
					elif second_base != "":
						away_runs += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
						away_hitting_stats[batter]['RBI'] += 1						
					elif third_base != "":
						away_runs += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base == ""
						away_hitting_stats[batter]['RBI'] += 1				
				elif event == "gb1b":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					#All runners advance one base on GB single
					if third_base != "":
						away_runs+=1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
					third_base = second_base
					second_base = first_base
					first_base = away_team_lineup[current_away_batter]				
				elif event == "ld1b":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					#Runners on 2nd and 3rd always score on LD single,
					#runner on 1st always goes to 3rd
					if third_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					first_base = away_team_lineup[current_away_batter]				
				elif event == "fb1b":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					#Runners on 2nd and 3rd always score on FB single,
					#runner on 1st DOES NOT go to 3rd
					if third_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						second_base = first_base
						first_base = ""
					first_base = away_team_lineup[current_away_batter]				
				elif event == "ldxb":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					away_hitting_stats[batter]['XB'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					#Bases clear on a line drive XB hit,
					#and all XB hits (any type) are doubles
					if third_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					if second_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					if first_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[first_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						first_base = ""
					second_base = away_team_lineup[current_away_batter]				
				elif event == "fbxb":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					away_hitting_stats[batter]['XB'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					if third_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					second_base = away_team_lineup[current_away_batter]				
				elif event == "gbxb":
					away_hits += 1
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['AB'] += 1
					away_hitting_stats[batter]['H'] += 1
					away_hitting_stats[batter]['XB'] += 1
					home_pitching_stats[pitcher]['H'] += 1
					if third_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						away_runs += 1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[second_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					second_base = away_team_lineup[current_away_batter]				
				elif event == "bb":
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['BB'] += 1
					home_pitching_stats[pitcher]['BB'] += 1
					if third_base != "":
						away_runs+=1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
					third_base = second_base
					second_base = first_base
					first_base = away_team_lineup[current_away_batter]				
				else:
					away_hitting_stats[batter]['PA'] += 1
					away_hitting_stats[batter]['HBP'] += 1
					home_pitching_stats[pitcher]['HBP'] += 1
					if third_base != "":
						away_runs+=1
						away_hitting_stats[batter]['RBI'] += 1
						away_hitting_stats[third_base]['R'] += 1
						home_pitching_stats[pitcher]['RA'] += 1
					third_base = second_base
					second_base = first_base
					first_base = away_team_lineup[current_away_batter]				
				#After batting event resolution, advance place in lineup
				#rotating back to the first batter when appropriate.
				if current_away_batter <8:
					current_away_batter += 1
				else:
					current_away_batter = 0
			#After 3 outs, switch to home batting
			away_team_at_bat = False
		else:
			#same as away stuff, but with inverted home/away
			inning_outs = 0
			first_base = ""
			second_base = ""
			third_base = ""
			while inning_outs<3:
				batter = home_team_lineup[current_home_batter]
				pitcher = away_team_pitchers[current_away_pitcher]
				set_odds(home_team_stats[batter],away_team_pstats[pitcher])
				event = PA_outcome()
				away_pitching_stats[pitcher]['TBF'] += 1
#				print("home event: "+event)
				if event == "iffb" or event == "gbout" or event == "fbout" or event == "ldout":
					outs += 1
					inning_outs += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					away_pitching_stats[pitcher]['Outs'] += 1
				elif event == "k":
					outs += 1
					inning_outs += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['K'] += 1
					away_pitching_stats[pitcher]['Outs'] += 1
					away_pitching_stats[pitcher]['K'] += 1
				elif event == "hr":
					home_runs += 1
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['R'] += 1
					home_hitting_stats[batter]['HR'] += 1
					home_hitting_stats[batter]['H'] += 1
					home_hitting_stats[batter]['RBI'] += 1
					home_hitting_stats[batter]['XB'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					away_pitching_stats[pitcher]['HR'] += 1
					away_pitching_stats[pitcher]['RA'] += 1
					if first_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[first_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						first_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						home_hitting_stats[batter]['RBI'] += 1
						second_base = ""						
					elif third_base != "":
						home_runs += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base == ""
						home_hitting_stats[batter]['RBI'] += 1				
				elif event == "gb1b":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					if third_base != "":
						home_runs+=1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
					third_base = second_base
					second_base = first_base
					first_base = home_team_lineup[current_home_batter]				
				elif event == "ld1b":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					if third_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					first_base = home_team_lineup[current_home_batter]				
				elif event == "fb1b":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					if third_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					first_base = home_team_lineup[current_home_batter]				
				elif event == "ldxb":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					home_hitting_stats[batter]['XB'] += 1
					if third_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[first_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						first_base = ""
					second_base = home_team_lineup[current_home_batter]				
				elif event == "fbxb":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					home_hitting_stats[batter]['XB'] += 1
					if third_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					second_base = home_team_lineup[current_home_batter]				
				elif event == "gbxb":
					home_hits += 1
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['AB'] += 1
					home_hitting_stats[batter]['H'] += 1
					away_pitching_stats[pitcher]['H'] += 1
					home_hitting_stats[batter]['XB'] += 1
					if third_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						third_base = ""
					elif second_base != "":
						home_runs += 1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[second_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
						second_base = ""
					elif first_base != "":
						third_base = first_base
						first_base = ""
					second_base = home_team_lineup[current_home_batter]				
				elif event == "bb":
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['BB'] += 1
					away_pitching_stats[pitcher]['BB'] += 1
					if third_base != "":
						home_runs+=1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
					third_base = second_base
					second_base = first_base
					first_base = home_team_lineup[current_home_batter]				
				else:
					home_hitting_stats[batter]['PA'] += 1
					home_hitting_stats[batter]['HBP'] += 1
					away_pitching_stats[pitcher]['HBP'] += 1
					if third_base != "":
						home_runs+=1
						home_hitting_stats[batter]['RBI'] += 1
						home_hitting_stats[third_base]['R'] += 1
						away_pitching_stats[pitcher]['RA'] += 1
					third_base = second_base
					second_base = first_base
					first_base = home_team_lineup[current_home_batter]
				if current_home_batter <8:
					current_home_batter += 1
				else:
					current_home_batter = 0
			away_team_at_bat = True
	#Old post-game printing:
	#print("Home runs: "+str(home_runs))
	#print("Home hits: "+str(home_hits))
	#print("Home avg: "+str(home_hits/(home_hits+3*inning)))
	#print("Away runs: "+str(away_runs))
	#print("Away hits: "+str(away_hits))
	#print("Away avg: "+str(away_hits/(away_hits+3*inning)))
	#print("Innings: "+str(inning))
	if(home_runs > away_runs):
		home_wins += 1
	else:
		away_wins += 1
	
#Main function. Sets lineups, establishes stat-keeping dictionaries and ints,
#asks how many games to simulate, and runs pbp() for that many. Shows player stats
#(messily, for now) and team wins at the end.	
def baseball_sim():
	build_rosters()
	global away_hitting_stats
	global home_hitting_stats
	global away_pitching_stats
	global home_pitching_stats
	global away_wins
	global home_wins
	away_hitting_stats = {}
	home_hitting_stats = {}
	away_pitching_stats = {}
	home_pitching_stats = {}
	away_wins = 0
	home_wins = 0
	for x in range(0,len(away_team_lineup)):
		batter_a = away_team_lineup[x]
		away_hitting_stats[batter_a] = {'PA':0,'AB':0,'H':0,'XB':0,'HR':0,'R':0,'RBI':0,'BB':0,'HBP':0,'K':0}
		batter_h = home_team_lineup[x]
		home_hitting_stats[batter_h] = {'PA':0,'AB':0,'H':0,'XB':0,'HR':0,'R':0,'RBI':0,'BB':0,'HBP':0,'K':0}
	for y in range(0,len(away_team_pitchers)):
		pitcher_a = away_team_pitchers[y]
		away_pitching_stats[pitcher_a] = {'TBF':0,'Outs':0,'H':0,'HR':0,'RA':0,'K':0,'BB':0,'HBP':0}
		pitcher_h = home_team_pitchers[y]
		home_pitching_stats[pitcher_h] = {'TBF':0,'Outs':0,'H':0,'HR':0,'RA':0,'K':0,'BB':0,'HBP':0}
	games = int(input("Number of games: "))
	i = 0
	while i < games:
		pbp()
		i += 1
	print(home_hitting_stats)
	print(home_pitching_stats)
	print(away_hitting_stats)
	print(away_pitching_stats)
	print("Home wins: "+str(home_wins))
	print("Away wins: "+str(away_wins))
	
baseball_sim()