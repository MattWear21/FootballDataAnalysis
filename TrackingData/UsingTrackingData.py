#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 22:04:03 2020

@author: mattwear
"""

###Tracking Data Assignment

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from Libraries import Functions_PreprocessTrackingData as funcs
from copy import deepcopy
from FCPython import createPitch
from scipy.spatial import Voronoi, voronoi_plot_2d

def remove_player_velocities(team):
    # remove player velocoties and acceleeration measures that are already in the 'team' dataframe
    columns = [c for c in team.columns if c.split('_')[-1] in ['vx','vy','ax','ay','speed','acceleration','disttogoal']] # Get the player ids
    team = team.drop(columns=columns)
    return team

def calc_player_velocities(team, maxspeed=12):
    """ calc_player_velocities( tracking_data )
    
    Calculate player velocities in x & y direciton, and total player speed at each timestamp of the tracking data
    
    Parameters
    -----------
        team: the tracking DataFrame for home or away team
        smoothing: boolean variable that determines whether velocity measures are smoothed. Default is True.
        filter: type of filter to use when smoothing the velocities. Default is Savitzky-Golay, which fits a polynomial of order 'polyorder' to the data within each window
        window: smoothing window size in # of frames
        polyorder: order of the polynomial for the Savitzky-Golay filter. Default is 1 - a linear fit to the velcoity, so gradient is the acceleration
        maxspeed: the maximum speed that a player can realisitically achieve (in meters/second). Speed measures that exceed maxspeed are tagged as outliers and set to NaN. 
        
    Returns
    -----------
       team : the tracking DataFrame with columns for speed in the x & y direction and total speed added

    """
    # remove any velocity data already in the dataframe
    team = remove_player_velocities(team)
    
    # Get the player ids
    player_ids = np.unique( [ c[:-2] for c in team.columns if c[:4] in ['Home','Away'] ] )

    # Calculate the timestep from one frame to the next. Should always be 0.04 within the same half
    dt = team['Time [s]'].diff()
    
    # estimate velocities for players in team
    for player in player_ids: # cycle through players individually
        # difference player positions in timestep dt to get unsmoothed estimate of velicity
        vx = team[player+"_x"].diff() / dt
        vy = team[player+"_y"].diff() / dt
        
        if maxspeed>0:
            # remove unsmoothed data points that exceed the maximum speed (these are most likely position errors)
            raw_speed = np.sqrt( vx**2 + vy**2 )
            vx[ raw_speed>maxspeed ] = np.nan
            vy[ raw_speed>maxspeed ] = np.nan
            
        #ax = vx / dt
        #ay = vy / dt
        
        
        # put player speed in x,y direction, and total speed back in the data frame
        team[player + "_vx"] = vx
        team[player + "_vy"] = vy
        team[player + "_speed"] = np.sqrt( vx**2 + vy**2 )
        #team[player + "_acceleration"] = np.sqrt( ax**2 + ay**2 )
        #Distance of player from opposition goal (x=0, y=34.2)
        if 'Home' in player:
            gx = 0
            gy = pitch_dimensions[1]/2
        else:
            gx = pitch_dimensions[0]
            gy = pitch_dimensions[1]/2
        dist = np.sqrt(np.square(team[player+"_x"]-gx)+np.square(team[player+"_y"]-gy))
        team[player + "_disttogoal"] = dist

    return team, player_ids

def calc_player_acceleration(team, player_ids, maxacc = 12):   
    # Calculate the timestep from one frame to the next. Should always be 0.04 within the same half
    dt = team['Time [s]'].diff()
    
    for player in player_ids:
    
        #Calculate acceleration vectors
        ax = team[player+"_vx"].diff() / dt
        ay = team[player+"_vy"].diff() / dt
        team[player + "_acceleration"] = np.sqrt( ax**2 + ay**2 )
    
    return team

#Added functionality to obtain match_time data
def LoadDataHammarbyCustom(data_file_name,raw_dir):
    print()
    print('Loading data, this might take some seconds...')
    
    info_dir = raw_dir+data_file_name+'-info_live.json'
    tracks_dir = raw_dir+data_file_name+'-tracks.json'
    events_dir = raw_dir+data_file_name+'-events.json'

    with open(info_dir) as json_data:
        info = json.load(json_data)

    with open(tracks_dir) as json_data:
        data = json.load(json_data)

    with open(events_dir) as json_data:
        events = json.load(json_data)
        
    # Add to info, so that is the same as the non-live
    info['home_team'] = {}
    info['home_team']['name'] = info['team_home_name']
    info['away_team'] = {}
    info['away_team']['name'] = info['team_away_name']
    
    pitch_dimensions = info['calibration']['pitch_size']

    #Get the track ids of all the players to stablish the order in the rest of arrays
    order_list = []
    players_jersey = []
    players_names = []
    players_team_id = []
    players_team_id_list = []

    
    track_id = 0
    for player in info['team_home_players']:
        order_list.append(track_id)
        players_jersey.append(player['jersey_number'])
        players_names.append(player['name'])
        players_team_id.append(2)
        num_players_home = len(order_list)
        track_id += 1
    for player in info['team_away_players']:
        order_list.append(track_id)
        players_jersey.append(player['jersey_number'])
        players_names.append(player['name'])
        players_team_id.append(7)
        num_players_away = len(order_list)-num_players_home
        track_id += 1
        
    num_players_total = num_players_home+num_players_away
    
    
    #Create the lists of arrays
    players_position = []
    ball_position = []
    match_time = []
    
    pitch_length = info['calibration']['pitch_size'][0]
    pitch_width = info['calibration']['pitch_size'][1]

    for frame in range(len(data)):
        match_time.append(data[frame]['match_time'])
        #Get position of ball for each frame
        if data[frame]['ball'].get('position',np.asarray([np.inf,np.inf,np.inf])) is None:
            bp = np.asarray([np.inf,np.inf,np.inf])
        else:
            bp = np.asarray(data[frame]['ball'].get('position',np.asarray([np.inf,np.inf,np.inf])))
        bp = np.delete(bp,-1)
        bp[0] = (bp[0]+pitch_length/2)/pitch_length
        bp[1] = (bp[1]+pitch_width/2)/pitch_width
        ball_position.append(bp)

        #Append arrays of positions
        players_position.append(np.full((num_players_total,2),-1.0))
            
        # Get players
        # Home players
        for player in range(len(data[frame]['home_team'])):
            try:
                jersey_player = int(data[frame]['home_team'][player].get('jersey_number',-1))
                position_player = np.asarray(data[frame]['home_team'][player].get('position',np.asarray([-1,-1])))
            except:
                jersey_player = -1
                position_player = np.asarray([-1,-1])
            
            try:
                idx = players_jersey[:num_players_home].index(jersey_player)
                players_position[frame][idx][0] = (position_player[0]+pitch_length/2)/pitch_length
                players_position[frame][idx][1] = (position_player[1]+pitch_width/2)/pitch_width
            except:
                pass

                
        for player in range(len(data[frame]['away_team'])):
            try:
                jersey_player = int(data[frame]['away_team'][player].get('jersey_number',-1))
                position_player = np.asarray(data[frame]['away_team'][player].get('position',np.asarray([-1,-1])))
            except:
                jersey_player = -1
                position_player = np.asarray([-1,-1])
            
            try:
                idx = players_jersey[num_players_home:].index(jersey_player)+num_players_home
                players_position[frame][idx][0] = (position_player[0]+pitch_length/2)/pitch_length
                players_position[frame][idx][1] = (position_player[1]+pitch_width/2)/pitch_width
            except:
                pass
        
        players_team_id_list.append(np.array(players_team_id))

    print('Data has been loaded')
    print()
    
    return ball_position,players_position,players_team_id_list,events,np.array(players_jersey),info,players_names,match_time,pitch_dimensions

#Custom Transform coordinates function with more precise pitch coords
def TransformCoordsCustom(players_pos,ball_pos, pd):
    #Transform co-ordinates to 105 and 68.
    pp = deepcopy(players_pos)
    bp = np.copy(ball_pos)
    
    for frame in range(len(players_pos)):
        pp[frame][:,0] = players_pos[frame][:,0]*pd[0]
        pp[frame][:,1] = players_pos[frame][:,1]*pd[1]
        bp[frame][0] = ball_pos[frame][0]*pd[0]
        bp[frame][1] = ball_pos[frame][1]*pd[1]

    return pp, bp

def getColNames(ti):
    xy = ["x" if i%2==0 else "y" for i in range(ti.shape[0]*2)] #x/y
    home_team = ti[0]
    ha = ["Home" if i==home_team else "Away" for i in ti] #Home/Away
    ha = np.repeat(ha, 2)
    pl = [i for i in range(1, len(ti)+1)]
    pl = np.repeat(pl, 2)
    #Use for loop and zip to combine these lists
    cols = []
    for i,j,k in zip(ha, pl, xy):
        s = i + '_' + str(j) + '_' + k
        cols.append(s)
    return cols

def plotFrame(home_team, away_team, frame, fignumber):
    (fig,ax) = createPitch(pitch_dimensions[0],pitch_dimensions[1],'yards','gray')
    team_colors=('r','b')
    PlayerMarkerSize = 12
    PlayerAlpha = 0.8
    for team,color in zip( [home_team.loc[frame],away_team.loc[frame]], team_colors) :
        x_columns = [c for c in team.keys() if c[-2:].lower()=='_x' and c!='ball_x'] # column header for player x positions
        y_columns = [c for c in team.keys() if c[-2:].lower()=='_y' and c!='ball_y'] # column header for player y positions
        ax.plot( team[x_columns], team[y_columns], color+'o', MarkerSize=PlayerMarkerSize, alpha=PlayerAlpha ) # plot player positions
        vx_columns = ['{}_vx'.format(c[:-2]) for c in x_columns] # column header for player x positions
        vy_columns = ['{}_vy'.format(c[:-2]) for c in y_columns] # column header for player y positions
        ax.quiver( team[x_columns], team[y_columns], team[vx_columns], team[vy_columns], color=color, scale_units='inches', scale=10.,width=0.003,headlength=5,headwidth=3,alpha=PlayerAlpha)
        #[ ax.text( team[x]+0.5, team[y]+0.5, x.split('_')[1], fontsize=10, color=color  ) for x,y in zip(x_columns,y_columns) if not ( np.isnan(team[x]) or np.isnan(team[y]) ) ] 
    # plot ball
    ax.plot( home_team.loc[frame]['ball_x'], away_team.loc[frame]['ball_y'], 'ko', MarkerSize=8, alpha=1.0, LineWidth=0, zorder=200)
    fig.set_size_inches(10, 7)
    fig.savefig('Output/frame'+str(fignumber)+'.png', dpi=100) 
    plt.show()
    
def save_match_clip(hometeam,awayteam, fpath, fname='clip_test', figax=None, frames_per_second=25, team_colors=('r','b'), field_dimen = (106.0,68.0), include_player_velocities=False, PlayerMarkerSize=10, PlayerAlpha=0.7):
    """ save_match_clip( hometeam, awayteam, fpath )
    
    Generates a movie from Metrica tracking data, saving it in the 'fpath' directory with name 'fname'
    
    Parameters
    -----------
        hometeam: home team tracking data DataFrame. Movie will be created from all rows in the DataFrame
        awayteam: away team tracking data DataFrame. The indices *must* match those of the hometeam DataFrame
        fpath: directory to save the movie
        fname: movie filename. Default is 'clip_test.mp4'
        fig,ax: Can be used to pass in the (fig,ax) objects of a previously generated pitch. Set to (fig,ax) to use an existing figure, or None (the default) to generate a new pitch plot,
        frames_per_second: frames per second to assume when generating the movie. Default is 25.
        team_colors: Tuple containing the team colors of the home & away team. Default is 'r' (red, home team) and 'b' (blue away team)
        field_dimen: tuple containing the length and width of the pitch in meters. Default is (106,68)
        include_player_velocities: Boolean variable that determines whether player velocities are also plotted (as quivers). Default is False
        PlayerMarkerSize: size of the individual player marlers. Default is 10
        PlayerAlpha: alpha (transparency) of player markers. Defaault is 0.7
        
    Returrns
    -----------
       fig,ax : figure and aixs objects (so that other data can be plotted onto the pitch)

    """
    # check that indices match first
    assert np.all( hometeam.index==awayteam.index ), "Home and away team Dataframe indices must be the same"
    # in which case use home team index
    index = hometeam.index
    # Set figure and movie settings
    FFMpegWriter = animation.writers['ffmpeg']
    metadata = dict(title='Tracking Data', artist='Matplotlib', comment='Metrica tracking data clip')
    writer = FFMpegWriter(fps=frames_per_second, metadata=metadata)
    fname = fpath + '/' +  fname + '.mp4' # path and filename
    # create football pitch
    if figax is None:
        (fig,ax) = createPitch(pitch_dimensions[0],pitch_dimensions[1],'yards','gray')
    else:
        fig,ax = figax
    fig.set_tight_layout(True)
    # Generate movie
    print("Generating movie...",end='')
    with writer.saving(fig, fname, 100):
        for i in index:
            figobjs = [] # this is used to collect up all the axis objects so that they can be deleted after each iteration
            for team,color in zip( [hometeam.loc[i],awayteam.loc[i]], team_colors) :
                x_columns = [c for c in team.keys() if c[-2:].lower()=='_x' and c!='ball_x'] # column header for player x positions
                y_columns = [c for c in team.keys() if c[-2:].lower()=='_y' and c!='ball_y'] # column header for player y positions
                objs, = ax.plot( team[x_columns], team[y_columns], color+'o', MarkerSize=PlayerMarkerSize, alpha=PlayerAlpha ) # plot player positions
                figobjs.append(objs)
                if include_player_velocities:
                    vx_columns = ['{}_vx'.format(c[:-2]) for c in x_columns] # column header for player x positions
                    vy_columns = ['{}_vy'.format(c[:-2]) for c in y_columns] # column header for player y positions
                    objs = ax.quiver( team[x_columns], team[y_columns], team[vx_columns], team[vy_columns], color=color, scale_units='inches', scale=10.,width=0.0015,headlength=5,headwidth=3,alpha=PlayerAlpha)
                    figobjs.append(objs)
            # plot ball
            objs, = ax.plot( team['ball_x'], team['ball_y'], 'ko', MarkerSize=6, alpha=1.0, LineWidth=0)
            figobjs.append(objs)
            # include match time at the top
            frame_minute =  int( team['Time [s]']/60. )
            frame_second =  ( team['Time [s]']/60. - frame_minute ) * 60.
            timestring = "%d:%1.2f" % ( frame_minute, frame_second  )
            objs = ax.text(-2.5,field_dimen[1]/2.+1., timestring, fontsize=14 )
            figobjs.append(objs)
            writer.grab_frame()
            # Delete all axis objects (other than pitch lines) in preperation for next frame
            for figobj in figobjs:
                figobj.remove()
    print("done")
    plt.clf()
    plt.close(fig)  
    
def plot_time_series(start, fignumber):
    frames_to_plot = 15 / 0.04
    home_players_total = int((len(home_tracking.columns)-3)/2)
    
    (fig, ax) = plt.subplots(nrows=3, ncols=1,figsize=(10,10))
    fig.subplots_adjust(hspace=0.2)
    for p in range(1,home_players_total+1):
        ax[0].plot(home_speeds['Time [s]'].loc[start:start+frames_to_plot]/60, home_speeds['Home_'+str(p)+'_disttogoal'].loc[start:start+frames_to_plot])
        ax[1].plot(home_speeds['Time [s]'].loc[start:start+frames_to_plot]/60, home_speeds['Home_'+str(p)+'_speed'].loc[start:start+frames_to_plot])
        ax[2].plot(home_speeds['Time [s]'].loc[start:start+frames_to_plot]/60, home_speeds['Home_'+str(p)+'_acceleration'].loc[start:start+frames_to_plot])
    #plt.ylim(0, 12)
    plt.xlabel('Time (minutes)')
    ax[0].set_ylabel('Distance to Opposition Goal (m)')
    ax[1].set_ylabel('Speed (m/s)')
    ax[2].set_ylabel('Acceleration (m/s/s)')
    fig.savefig('Output/timeseries'+str(fignumber)+'.png', dpi=100)
    plt.tight_layout()
    plt.show()
    
def plotVoronoi(home_team, away_team, frame, fignumber):
    (fig,ax) = createPitch(pitch_dimensions[0],pitch_dimensions[1],'yards','gray')
    team_colors=('r','b')
    PlayerMarkerSize = 12
    PlayerAlpha = 0.8
    for team,color in zip( [home_team.loc[frame],away_team.loc[frame]], team_colors) :
        x_columns = [c for c in team.keys() if c[-2:].lower()=='_x' and c!='ball_x'] # column header for player x positions
        y_columns = [c for c in team.keys() if c[-2:].lower()=='_y' and c!='ball_y'] # column header for player y positions
        ax.plot( team[x_columns], team[y_columns], color+'o', MarkerSize=PlayerMarkerSize, alpha=PlayerAlpha ) # plot player positions
        vx_columns = ['{}_vx'.format(c[:-2]) for c in x_columns] # column header for player x positions
        vy_columns = ['{}_vy'.format(c[:-2]) for c in y_columns] # column header for player y positions
        ax.quiver( team[x_columns], team[y_columns], team[vx_columns], team[vy_columns], color=color, scale_units='inches', scale=10.,width=0.003,headlength=5,headwidth=3,alpha=PlayerAlpha)
        [ ax.text( team[x]+0.5, team[y]+0.5, x.split('_')[1], fontsize=10, color=color  ) for x,y in zip(x_columns,y_columns) if not ( np.isnan(team[x]) or np.isnan(team[y]) ) ] 
    # plot ball
    ax.plot( home_team.loc[frame]['ball_x'], away_team.loc[frame]['ball_y'], 'ko', MarkerSize=8, alpha=1.0, LineWidth=0, zorder=200)
    points = players_position[frame]
    #points = np.nan_to_num(points, nan=0)
    points_new = []

    for i in points:
        if np.isnan(i)[0] == False:
            points_new.append(list(i))
    vor = Voronoi(points_new)
    voronoi_plot_2d(vor, ax, point_size = 0.01)
    fig.set_size_inches(10, 7)
    fig.savefig('Output/voronoi'+str(fignumber)+'.png', dpi=100) 
    plt.tight_layout()
    plt.show()

file_name = '20190722.Hammarby-IFElfsborg'

#Names of the teams playing in OPTA format
home_team_name = 'Hammarby IF'
away_team_name = 'IF Elfsborg'
year = file_name[:4]

#First '.1' or second '.2' half of the match
data_file_name=file_name+'.1'

#Preprocesses the file in to the format we use.
#Using my own custom function which also obtains match_time data 
if not os.path.exists('../Signality/'+year+'/Tracking Data/Preprocessed/'+data_file_name+'_preprocessed.pickle'):
    preprocessed = False
    [ball_position_not_transf,players_position_not_transf,players_team_id,events,players_jersey,
     info_match,names_of_players,match_time,pitch_dimensions] = LoadDataHammarbyCustom(data_file_name,'Signality/2019/Tracking Data/')
else:
    preprocessed = True
    [ball_position_not_transf,players_position_not_transf,players_team_id,events,players_jersey,
     info_match,names_of_players,players_in_play_list] = funcs.LoadDataHammarbyPreprocessed(data_file_name,'Signality/2019/Tracking Data/')

frame=1000

team_index = players_team_id[frame].astype(int).reshape(len(players_team_id[frame]),)

#Need to convert coordinates to nan when they are not in play
print("Cleaning player coordinates. This may take a few minutes.")
total_players = len(players_position_not_transf[frame])
all_players = list(range(0,total_players))
for frame in range(len(players_position_not_transf)):
    players_in_play = funcs.GetPlayersInPlay(players_position_not_transf,frame)
    players_not_in_play = np.setdiff1d(all_players, players_in_play)
    players_position_not_transf[frame][players_not_in_play] = [np.nan, np.nan]

#Transform coordinates
[players_position,ball_position] = TransformCoordsCustom(players_position_not_transf,ball_position_not_transf, pitch_dimensions)

#Convert players_position and ball_position lists to df in form of tracking_home (Metrica dataset)
reshaped = np.reshape(players_position, (len(players_position), len(players_position[0])*2))
bp_df = pd.DataFrame(ball_position, columns=["ball_x","ball_y"]) #Ball position

#Players positions dataframe
pp_df = pd.DataFrame(reshaped, columns = getColNames(team_index)) #Player position - SORT OUT COLUMN NAMES
#Home and away tracking datasets
home_tracking = pp_df.loc[:,pp_df.columns.str.contains("Home")]
away_tracking = pp_df.loc[:,pp_df.columns.str.contains("Away")]


#Combine pp_df(player position), bp_df (ball pos) and match_time into one df
match_time = pd.Series(match_time, name="Time [s]")
match_time = match_time * 0.001
tracking_df = pd.concat([match_time, pp_df, bp_df], axis=1)
home_tracking = pd.concat([match_time, home_tracking, bp_df], axis=1)
away_tracking = pd.concat([match_time, away_tracking, bp_df], axis=1)

#Calculate player velocities and distance to goal
tracking_speeds, pids = calc_player_velocities(tracking_df)

#Calculate acceleration
tracking_speeds = calc_player_acceleration(tracking_speeds, pids)

#Filter tracking speeds for home and away
home_cols = [col for col in tracking_speeds.columns if 'Home' in col]
home_cols.append('Time [s]')
home_cols.append('ball_x')
home_cols.append('ball_y')
home_speeds = tracking_speeds.loc[:,home_cols]

away_cols = [col for col in tracking_speeds.columns if 'Away' in col]
away_cols.append('Time [s]')
away_cols.append('ball_x')
away_cols.append('ball_y')
away_speeds = tracking_speeds.loc[:,away_cols]

#Plot Match Situation
plotFrame(home_speeds, away_speeds, frame=3900, fignumber=1)
plotFrame(home_speeds, away_speeds, frame=55, fignumber=2)
plotFrame(home_speeds, away_speeds, frame=51000, fignumber=3)
plotFrame(home_speeds, away_speeds, frame=2344, fignumber=4)

#Plot distance to goal, speed and acceleration of all Hammarby players

plot_time_series(10000, fignumber=1)
plot_time_series(30000, fignumber=2)
plot_time_series(11000, fignumber=3)


#Number 16 goalscorer's movement creates Voronoi corridor passing straight
#through the goal, when just a second prior he was well marked and in tight space
plotVoronoi(home_speeds, away_speeds, frame=26780, fignumber=1)
plotVoronoi(home_speeds, away_speeds, frame=26830, fignumber=2)

#Robert Gojani, number 16, index 31
own_team = players_position[26780][25:]
other_team = players_position[26780][7:18]
own_team2 = players_position[26830][25:]
other_team2 = players_position[26830][7:18]

#Distance to teammates in frame 26780
gojani_pos = own_team[6]
distance_to_players = np.sqrt((gojani_pos[0] - own_team[:,0])**2 + (gojani_pos[1] - own_team[:,1])**2)

#Distance to teammates in frame 26830
gojani_pos2 = own_team2[6]
distance_to_players2 = np.sqrt((gojani_pos2[0] - own_team2[:,0])**2 + (gojani_pos2[1] - own_team2[:,1])**2)

#Distance to opposition in frame 26780
distance_to_opp = np.sqrt((gojani_pos[0] - other_team[:,0])**2 + (gojani_pos[1] - other_team[:,1])**2)

#Distance to opposition in frame 26830
distance_to_opp2 = np.sqrt((gojani_pos2[0] - other_team2[:,0])**2 + (gojani_pos2[1] - other_team2[:,1])**2)






