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
    get_id, get_multipolygon, get_line_dist

#column titles for the df we will create
BLOCK = 'block_group'
DISTANCE = 'distance'
NAME = 'location_name'

#a dataframe that will store how much distance a location is in a block group
DISTANCE_DF = {NAME: [],
               BLOCK: [],
               DISTANCE: []}

#a dataframe that holds which locations are a single point and what blockgroup
#they are in
SINGLE_PT_DF = {NAME: [],
               BLOCK: []}

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
    df = pd.read_csv('unique_locations_with_endpoint_blockgroups.csv')
    #load all blockgroup data
    blockgroup_df = pd.read_csv('blkgrps_2019_clipped.csv')

    #clean the data
    #there are some extra columns we want to get rid of
    df = df[['location_name','from', 'to', 'from_lat_long', 'to_lat_long',\
           'from_blockgroup', 'to_blockgroup']]

    #a list of the locations that have errors
    error_lst = []

    for index, row in df.iterrows():
        #get the pertinent information from the row
        name = row[0]
        from_pt = get_floats(row[3])
        to_pt = get_floats(row[4])
        blockgroup1_id, one_tf = get_id(row[5])
        if one_tf:
            blockgroup1_multipolygon = get_multipolygon(blockgroup1_id,\
                blockgroup_df)
        blockgroup2_id, two_tf = get_id(row[6])
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
                SINGLE_PT_DF[NAME].append(name)
                SINGLE_PT_DF[BLOCK].append(blockgroup1_id)
                error = False
            else:
                error = True
        #check if either block group is a string (means it doesn't have a
        #block group
        elif type(blockgroup1_id) == str or type(blockgroup2_id) == str:
            error = check_all_bg(line, distance, name, blockgroup_df)
        #check if we begin and end in the same blockgroup
        elif blockgroup1_id == blockgroup2_id:
            error = same_from_to_add(line,\
                blockgroup1_multipolygon, blockgroup1_id, distance, name, \
                blockgroup_df)
        else:
            error = diff_from_to_add(line,\
                blockgroup1_multipolygon,\
                blockgroup2_multipolygon, blockgroup1_id, blockgroup2_id,\
                distance, name, blockgroup_df)

        if error:
            #if there is an error, add the index to our list of errors
            error_lst.append(name)

    df.loc[df['location_name'].isin(error_lst)].to_csv('locations_errors.csv')
    pd.DataFrame(data=DISTANCE_DF).to_csv('locations_w_parsed_distances.csv')
    pd.DataFrame(data=SINGLE_PT_DF).to_csv('single_point_locations.csv')

def loop_through_loc_df(dist_dict, name):
    '''
    Loops through a location dataframe and adds the various block groups and
    distances that are associated with that location to the final df

    Inputs:
        dist_dict: a disctionary with the distance that the location passes
            through a given blockgroup
        name: (string) the location name
    '''
    for blockgroup, distance in dist_dict.items():
        add_to_df(blockgroup, distance, name)

def add_to_df(block, dist, name):
    '''
    Adds a single entry to the final df

    Inputs:
        block: (int) the blockgroup id
        dist: (float) the number of kilometers the given project has
            passed throigh the blockgroup (for a given location)
        name: (string) the location name

    Outputs: none, it writes our data directly to our dataframe
    '''
    DISTANCE_DF[NAME].append(name)
    DISTANCE_DF[BLOCK].append(block)
    DISTANCE_DF[DISTANCE].append(dist)

def same_from_to_add(line, blockgroup_multipolygon, \
    blockgroup_id, distance, name, blockgroup_df):
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
        blockgroup_id: (int) the blockgroup id for the blockgroup the line
            begins and ends in
        distance: (float) the length (in km) of the line
        name: (string) the location name
        blockgroup_df: dataframe with the multipolygon information about all
            of the blockgroups

    Outputs:
        error: (boolean) if there was an error in finding the distance
    '''

    try:
        #attempt to find the intersection line in the blockgroup
        intersection = line.intersection(blockgroup_multipolygon)
    except:
        #if we can't get an intersection,we will add to the error_df
        return(True)
        
    #if the intersection line is a single LineString and it equals
    #the original line, we know the entire location is in the blockgroup
    if type(intersection) == LineString and line == intersection:
        loop_through_loc_df({str(blockgroup_id): distance}, name)
        return(False)
    else:
        return(check_all_bg(line, distance, name, blockgroup_df))

def diff_from_to_add(line, blockgroup1_multipolygon, blockgroup2_multipolygon,\
   blockgroup1_id, blockgroup2_id, distance, name, blockgroup_df):
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
        blockgroup1_id: (int) the blockgroup id for the blockgroup the line
            begins in
        blockgroup2_id: (int) the blockgroup id for the blockgroup the line
            ends in
        distance: (float) the length (in km) of the line
        name: (string) the location name
        blockgroup_df: dataframe with the multipolygon information about all
            of the blockgroups

    Outputs:
        error: (boolean) if there was an error in finding the distance
    '''
    try:
        #get the intersection lines with the multipolygon
        intersection1 = line.intersection(blockgroup1_multipolygon)
        intersection2 = line.intersection(blockgroup2_multipolygon)
    except:
        #if we can't get an intersection,we will add to the error_df
        return(True)

    #make sure we did not get a series back
    if type(intersection1) == LineString and type(intersection2) == LineString:
        #get the distance of both lines
        dist1 = get_line_dist(intersection1)
        dist2 = get_line_dist(intersection2)
        #check that the distances of the two intersection lines are within 1
        #meter of the total distance
        if abs(distance - (dist1 + dist2)) < 0.001:
            #add the values and distances to the final dataframe
            dist_dict = {str(blockgroup1_id): dist1,\
                str(blockgroup2_id): dist2}
            loop_through_loc_df(dist_dict, name)
            return(False)
        else:
            return(check_all_bg(line, distance, name, blockgroup_df))
    else:
        return(check_all_bg(line, distance, name, blockgroup_df))

def check_all_bg(line, distance, name, blockgroup_df):
    '''
    Goes through all the blockgroups and sees which if the given line
    intersects with it. If a line intersects with a blockgroup, adds the
    distance to the final_df

    Inputs:
        line: (LineString) the line between the beginning and ending points
        distance: (float) the length (in km) of the line
        name: (string) the location name
        blockgroup_df: a dataframe with all the blockgroup information

    Outputs:
        error: (boolean) if there was an error in finding the distance
    '''
    #create a list of dictionaries of the lines that make up the larget line
    bg_line_lst = []
    #iterate through the blockgroups
    for bg_index, bg_row in blockgroup_df.iterrows():
        blockgroup_id = bg_row[2]
        mp = convert_multipolygon(bg_row[1])
        #iterate through all the entries we need to check
        if line.intersects(mp):
            #try to find the intersection line
            try:
                intersection = line.intersection(mp)
            except:
                return(True)

            if type(intersection) == LineString:
                lines_lst = [intersection]
            elif type(intersection) == Point:
                lines_lst = []
            else:
                lines_lst = list(intersection)
            for this_line in lines_lst:
                this_line_dist = get_line_dist(this_line)
                #create a dictionary to hold information about this line
                line_dict = {'blockgroup_id': str(blockgroup_id),\
                    'line': this_line, 'full_distance': this_line_dist, \
                    'to_half': 0}
                #see if the current line intersects with a previous line
                for prev_line_dict in bg_line_lst:
                    prev_line = prev_line_dict['line']
                    if this_line.intersects(prev_line):
                        try:
                            line_intersection = \
                                this_line.intersection(prev_line)
                        except:
                            return(True)
                        if type(line_intersection) == LineString:
                            intersection_distance = \
                                get_line_dist(line_intersection)
                            #if the lines intersect, each blockgroup gets half
                            #the distance
                            prev_line_dict['to_half'] += intersection_distance
                            line_dict['to_half'] += intersection_distance
                bg_line_lst.append(line_dict)
    
    #create the distance dictionary from all the lines we have found
    dist_dict = {}
    total_length = 0
    for line_dict in bg_line_lst:
        blockgroup_id = line_dict['blockgroup_id']
        full_distance = line_dict['full_distance']
        to_half = line_dict['to_half']
        this_distance = (full_distance - to_half) + (0.5 * to_half)
        dist_dict[blockgroup_id] = dist_dict.get(blockgroup_id, 0) +\
            this_distance
        total_length += this_distance

    diff = abs(total_length - distance)
    #if the difference between the length of the line and what we got
    #is greater than 10 meters, we say it is an error
    if diff > 0.01:
        return(True)

    else:
        loop_through_loc_df(dist_dict, name)

    return(False)

