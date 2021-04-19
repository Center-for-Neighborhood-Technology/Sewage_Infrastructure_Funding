'''
Author: Esther Edith Spurlock

Title: Find Length

Organization: Center for Neighborhood Technology

Purpose: Find out the length a location passes through a blockgroup
'''

import pandas as pd
from shapely.geometry import Point, Polygon, LineString
from geopy.distance import great_circle
from helper_functions import convert_multipolygon, create_point, get_floats,\
    get_id

#column titles for the df we will create
PROJECT = 'project_number'
YEAR = 'year_range'
BLOCK = 'block_group'
DISTANCE = 'distance'

#a dataframe that will store how much distance a project is in a block group
DISTANCE_DF = {PROJECT: [],
               YEAR: [],
               BLOCK: [],
               DISTANCE: []}

def main():
    '''
    The main of the file

    !!!Better description to come later
    '''
    #load in data linking locations to blockgroups
    df = pd.read_csv('locations_with_endpoint_blockgroups_prelim.csv')
    #load all blockgroup data
    blockgroup_df = pd.read_csv('blkgrps_2019_clipped.csv')

    #clean the data
    #there are some extra columns we want to get rid of
    df = df[['project_number', 'location_name',\
           'year_range', 'from', 'to', 'from_lat_long', 'to_lat_long',\
           'from_blockgroup', 'to_blockgroup']]

    #a list of the locations that have errors
    error_lst = []

    for index, row in df.iterrows():
        #get the pertinent information from the row
        proj_num = row[0]
        years = row[2]
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

        #check if the 2nd blockgroup is None or distance is 0
        #means we have a single point and we are coding the distance as a 
        #pre-determined length
        if blockgroup2_id == 'None' or distance == 0.0:
            #make sure the 1st blockgroup is valid
            if type(blockgroup1_id) == int:
                add_to_df(proj_num, years, blockgroup1_id, 0.001)
                error = False
            else:
                error = True
        #check if either block group is a string (means it doesn't have a
        #block group
        elif type(blockgroup1_id) == str or type(blockgroup2_id) == str:
            error = True
        #check if we begin and end in the same blockgroup
        elif blockgroup1_id == blockgroup2_id:
            error = same_from_to_add(line, blockgroup1_multipolygon, proj_num,\
                years, blockgroup1_id, distance, blockgroup_df)
        else:
            error = diff_from_to_add(line, blockgroup1_multipolygon,\
                blockgroup2_multipolygon, proj_num, years,\
                blockgroup1_id, blockgroup2_id, distance, blockgroup_df)

        if error:
            #if there is an error, add the index to our list of errors
            error_lst.append(index)
    
    final_df = pd.DataFrame(data=DISTANCE_DF)
    print(error_lst)
    error_df = df.iloc[error_lst, :]
    return(final_df, error_df)

def add_to_df(proj, years, block, dist):
    '''
    Adds a single entry to the final df

    !!!Better description plus inputs and outputs come later
    '''
    DISTANCE_DF[PROJECT].append(proj)
    DISTANCE_DF[YEAR].append(years)
    DISTANCE_DF[BLOCK].append(block)
    DISTANCE_DF[DISTANCE].append(dist)

def same_from_to_add(line, blockgroup_multipolygon, proj_num, years,\
    blockgroup_id, distance, blockgroup_df):
    '''
    Scenario 2: the beginning and ending points are in the same block group
        this scenario has 2 sub-scenarios
        scenario has 1,829 occurrences
        Sub-Scenario 1: the location remains in the block group for all its
        length
            in this sub-scenario, we will find the length of the whole line
            and attribute it to the single block group
        Sub-Scenario 2: the location intersects with the block group at some 
        point
            in this sub-scenario, we will have to find out which other block
            groups the location intersects with and determine the length
            in each block group
    !!!Better description plus inputs and outputs come later
    '''

    #iterate through the rows and add them to the dataframe
    try:
        #attempt to find the intersection line in the blockgroup
        intersection = line.intersection(blockgroup_multipolygon)
    except:
        #if we can't get an intersection,we will add to the error_df
        return(True)
        
    #if the intersection line is a single LineString and it equals
    #the original line, we know the entire location is in the blockgroup
    if type(intersection) == LineString and line == intersection:
        add_to_df(proj_num, years, blockgroup_id, distance)
        return(False)
    else:
        #!!!need to send to other function to find all the dfs it
        #!!!intersects with
        return(False)

def diff_from_to_add(line, blockgroup1_multipolygon, blockgroup2_multipolygon,\
   proj_num, years, blockgroup1_id, blockgroup2_id, distance, blockgroup_df):
    '''
    #Scenario 3: the beginning and ending points are in different block groups
    #in this scenario, we will need to find out where it intersects with the
    #two block groups. If the location intersects with each block group only
    #once and those points have the same latitude and longitude, then
    #we can safely say that the length in each block group is the length from
    #the point inside the block group to the intersection point
    #however, if the intersection points do not match up, then we will need to
    #find which other block groups the location intersects with and we will
    #find the length the location is in each block group using a similar method
    #to what has just been described
    #scenario has 2,013 occurrences (including records where we do not have
    #the blockgroup)

    !!!Better description plus inputs and outputs come later
    '''
    #list(line.coords) gives a list of tuples of a line's endpoints
    return(False)

def get_multipolygon(blockgroup_id, blockgroup_df):
    '''
    #get a single blockgroup
    !!!Better description plus inputs and outputs come later
    '''
    blockgroup = blockgroup_df.\
        loc[blockgroup_df['stfid']==blockgroup_id, 'geom'].iloc[0]
    return(convert_multipolygon(blockgroup))

