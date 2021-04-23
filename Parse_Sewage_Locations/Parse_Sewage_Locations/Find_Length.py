'''
Author: Esther Edith Spurlock

Title: Find Length

Organization: Center for Neighborhood Technology

Purpose: Find out the length a location passes through a blockgroup
'''

import pandas as pd
from shapely.geometry import Point, Polygon, LineString, MultiLineString
from geopy.distance import great_circle
from helper_functions import convert_multipolygon, create_point, get_floats,\
    get_id, get_multipolygon

#column titles for the df we will create
PROJECT = 'project_number'
YEAR = 'year_range'
BLOCK = 'block_group'
DISTANCE = 'distance'
NAME = 'location_name'

#a dataframe that will store how much distance a project is in a block group
DISTANCE_DF = {PROJECT: [],
               YEAR: [],
               NAME: [],
               BLOCK: [],
               DISTANCE: []}

def main():
    '''
    The main of the file

    This function pulls in the necessary data, cleans it, and then iterates
    through the data and sends each record to the appropriate function to
    find the length a location passes through a blockgroup

    Inputs: none; it reads data from previously created CSVs

    Outputs:
        final_df: a dataframe that indicates how far a project in a given year
            travels in a given blockgroup (only for clean data)
        error_df: a data frame that indicates which records we were not able 
            to find any distance for
        errors_w_bgs: a data frame that indicates which records we were not
            able to find distance within the indicated blockgroup
    '''
    #load in data linking locations to blockgroups
    df = pd.read_csv('locations_with_endpoint_blockgroups_prelim.csv')
    #load in the information about quality
    quality_df = pd.read_csv('locations_with_quality.csv').fillna('None')
    #grab the locations that have errors in them
    error_locations = quality_df['all_locations'].loc[quality_df['quality'].\
        isin(['RoadBlock','PopulatedPlace','None','RailwayStation'])].tolist()
    #load all blockgroup data
    blockgroup_df = pd.read_csv('blkgrps_2019_clipped.csv')

    #clean the data
    #there are some extra columns we want to get rid of
    df = df[['project_number', 'location_name',\
           'year_range', 'from', 'to', 'from_lat_long', 'to_lat_long',\
           'from_blockgroup', 'to_blockgroup']]
    
    #remove the locations that have errors in them
    df_clean = df.loc[~df[['from', 'to']].isin(error_locations).any(axis=1)]
    
    del(quality_df)
    del(error_locations)

    #a list of the locations that have errors
    error_lst = []

    #get a list of all the locations
    full_locations = df_clean['location_name'].unique().tolist()

    print('Going through initial iterrows')
    for name in full_locations:
        #get a df with all the records for this location
        this_loc_df = df_clean.loc[df_clean['location_name']==name]
        #pull out the first row with the location
        row = this_loc_df[0]
        #get the pertinent information from the row
        from_pt = get_floats(row[5])
        to_pt = get_floats(row[6])
        blockgroup1_id, one_tf = get_id(row[7])
        if one_tf:
            blockgroup1_multipolygon = get_multipolygon(blockgroup1_id,\
                blockgroup_df)
        blockgroup2_id, two_tf = get_id(row[8])
        if two_tf:
            blockgroup2_multipolygon = get_multipolygon(blockgroup2_id,\
                blockgroup_df)

        if to_pt != 'None':
            #create a line between the endpoints
            line = LineString([from_pt, to_pt])
            #get the distance of the whole line
            distance = great_circle(from_pt, to_pt).km
        
        error = False
        #check if the 2nd blockgroup is None means we have a single point and
        #we are coding the distance as a pre-determined length
        if blockgroup2_id == 'None':
            #make sure the 1st blockgroup is valid
            if type(blockgroup1_id) == int:
                add_to_df(this_loc_df, {blockgroup1_id: 0.001}, name)
                error = False
            else:
                error = True
        #check if either block group is a string (means it doesn't have a
        #block group
        elif type(blockgroup1_id) == str or type(blockgroup2_id) == str:
            #!!!Writing it this way means that if a location is on the 
            #!!!border of 2 blockgroups, we will count the entire
            #!!!distance for both block groups, instead of cutting the
            #!!!distance in half as Peter wanted
            check_all = True
        #check if we begin and end in the same blockgroup
        elif blockgroup1_id == blockgroup2_id:
            error, check_all = same_from_to_add(line,\
                blockgroup1_multipolygon, proj_num,\
                years, blockgroup1_id, distance, name)
        else:
            error, check_all = diff_from_to_add(line,\
                blockgroup1_multipolygon,\
                blockgroup2_multipolygon, proj_num, years,\
                blockgroup1_id, blockgroup2_id, distance, name)

        if error:
            #if there is an error, add the index to our list of errors
            error_lst.append(name)

    error_df = df_clean.loc[df_clean['location_name'].isin(error_lst)]
    final_df = pd.DataFrame(data=DISTANCE_DF)
    return(final_df, error_df)

def loop_through_loc_df(this_loc_df, dist_dict, name):
    '''
    Loops through a location dataframe and adds the various block groups and
    distances that are associated with that location to the final df

    !!!Better description plus inputs and outputs come later
    '''
    for index, row in this_loc_df.iterrows():
        for blockgorup, distance in dist_dict.items():

def add_to_df(proj, years, block, dist, name):
    '''
    Adds a single entry to the final df

    Inputs:
        proj: (string) the project number
        years: (string) the year range for the project
        block: (int) the blockgroup id
        dist: (float) the number of kilometers the given project has
            passed throigh the blockgroup (for a given location)

    Outputs: none, it writes our data directly to our dataframe
    '''
    DISTANCE_DF[PROJECT].append(proj)
    DISTANCE_DF[YEAR].append(years)
    DISTANCE_DF[NAME].append(name)
    DISTANCE_DF[BLOCK].append(block)
    DISTANCE_DF[DISTANCE].append(dist)

def same_from_to_add(line, blockgroup_multipolygon, proj_num, years,\
    blockgroup_id, distance, name):
    '''
    This function looks at the scenario where a line begins and ends in the
    same block group. Checks to make sure the line never exits the block
    group and if it does not, adds the ditance information to the final df. If
    the line does exit the block group, indicates that we need to check all
    other block groups.

    Inputs:
        line: (LineString) the line between the beginning and ending points
        blockgroup_multipolygon: (Polygon) the polygon representation of the
            blockgroup that the line begins and ends in
        proj_num: (string) the project number
        years: (string) the year range for the project
        blockgroup_id: (int) the blockgroup id for the blockgroup the line
            begins and ends in
        distance: (float) the length (in km) of the line

    Outputs:
        error: (boolean) if there was an error in finding the distance
        check_all: (boolean) if we need to check all the blockgroups
            to see if this line passes through them
    '''

    try:
        #attempt to find the intersection line in the blockgroup
        intersection = line.intersection(blockgroup_multipolygon)
    except:
        #if we can't get an intersection,we will add to the error_df
        return(True, False)
        
    #if the intersection line is a single LineString and it equals
    #the original line, we know the entire location is in the blockgroup
    if type(intersection) == LineString and line == intersection:
        add_to_df(proj_num, years, blockgroup_id, distance, name)
        return(False, False)
    else:
        return(False, True)

def diff_from_to_add(line, blockgroup1_multipolygon, blockgroup2_multipolygon,\
   proj_num, years, blockgroup1_id, blockgroup2_id, distance, name):
    '''
    This function looks at the scenario where the line begins and ends in two
    separate block groups. Checks to see if the lines pass through only those
    two block groups. If the line is contained in just the beginning and ending
    block groups, adds the distance information to the final dataframe. if not,
    indicates that we need to check all block groups to see if the line
    passes through it.

    Inputs:
        line: (LineString) the line between the beginning and ending points
        blockgroup1_multipolygon: (Polygon) the polygon representation of the
            blockgroup that the line begins in
        blockgroup2_multipolygon: (Polygon) the polygon representation of the
            blockgroup that the line ends in
        proj_num: (string) the project number
        years: (string) the year range for the project
        blockgroup1_id: (int) the blockgroup id for the blockgroup the line
            begins in
        blockgroup2_id: (int) the blockgroup id for the blockgroup the line
            ends in
        distance: (float) the length (in km) of the line

    Outputs:
        error: (boolean) if there was an error in finding the distance
        check_all: (boolean) if we need to check all the blockgroups
            to see if this line passes through them
    '''
    try:
        #get the intersection lines with the multipolygon
        intersection1 = line.intersection(blockgroup1_multipolygon)
        intersection2 = line.intersection(blockgroup2_multipolygon)
    except:
        #if we can't get an intersection,we will add to the error_df
        return(True, False)

    #make sure we did not get a series back
    if type(intersection1) == LineString and type(intersection2) == LineString:
        #get the coordinates from the intersection strings
        from1, to1 = list(intersection1.coords)
        from2, to2 = list(intersection2.coords)
        #get the distance of both lines
        dist1 = great_circle(from1, to1).km
        dist2 = great_circle(from2, to2).km
        #check that the distances of the two intersection lines are within 1
        #meter of the total distance
        if abs(distance - (dist1 + dist2)) < 0.001:
            #add the values and distances to the final dataframe
            for tup in [(blockgroup1_id, dist1),(blockgroup2_id, dist2)]:
                block, dist = tup
                add_to_df(proj_num, years, block, dist, name)
            return(False, False)
        else:
            return(False, True)
    else:
        return(False, True)

def check_all_bg(check_all_df, blockgroup_df):
    '''
    Goes through all the blockgroups and sees which of the lines we have marked
    intersects with it. If a line intersects with a blockgroup, adds the the
    distance to the final_df

    Inputs:
        check_all_df: a dataframe with all the lines that we need to check all
            blockgroups for
        blockgroup_df: a dataframe with all the blockgroup information

    Outputs:
        error_lst: a list of indexes of locations where there were errors for
            one or more blockgroup
        error_blockgroups: a list of blockgroup ids where there were errors
            finding the intersecting line
    '''
    #a list of all the error entries there are
    error_lst = []
    #a list of the blockgroup id where the errors occur
    error_blockgroups = []
    #iterate through the blockgroups
    for bg_index, bg_row in blockgroup_df.iterrows():
        blockgroup_id = bg_row[2]
        print(blockgroup_id)
        mp = convert_multipolygon(bg_row[1])
        #iterate through all the entries we need to check
        for line_index, line_row in check_all_df.iterrows():
            proj_num = line_row[0]
            name = line_row[1]
            years = line_row[2]
            line = line_row[9]
            #check if the line intersects the blockgroup
            if line.intersects(mp):
                #try to find the intersection line
                try:
                    intersection = line.intersection(mp)
                    error = False
                except:
                    error_lst.append(line_index)
                    error_blockgroups.append(blockgroup_id)
                    error = True
                if not error:
                     if type(intersection) == LineString:
                         lines_lst = [intersection]
                     elif type(intersection) == Point:
                         print(name)
                         lines_lst = []
                     else:
                         lines_lst = list(intersection)
                     for l in lines_lst:
                         from_pt, to_pt = list(l.coords)
                         distance = great_circle(from_pt, to_pt).km
                         add_to_df(proj_num, years, blockgroup_id, distance,\
                             name)

    return(error_lst, error_blockgroups)

