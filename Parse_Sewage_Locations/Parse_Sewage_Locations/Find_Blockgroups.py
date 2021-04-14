'''
Author: Esther Edith Spurlock

Title: Find Blockgroups

Organization: Center for Neighborhood Technology

Purpose: Find out which blockgroups a location starts and ends in
'''

import pandas as pd
from shapely.geometry import Point, Polygon
from helper_functions import convert_multipolygon, create_point

def main():
    '''
    Determines the blockgroups of the beginning and endpoints of our
    locations. Saves the results to a csv file.
    '''
    #we have already created a csv of our locations with their lat and long
    #!!!the lat and long list I stored here is stored as a string
    #!!!needs to be converted black to list of floats
    sewage_locations = pd.read_csv('locations_with_lat_long.csv')\
        .fillna('None')
    #we have already downloaded the blockgroups data
    blockgroups = pd.read_csv('blkgrps_2019_clipped.csv')

    #create new columns to hold which blockgroups the endpoints are in
    for col in ['from_lat_long', 'to_lat_long']:
        new_col = col.split('_')[0] + '_blockgroup'
        sewage_locations[new_col] = sewage_locations[col]

    #iterate through the blockgroups
    for index, row in blockgroups.iterrows():
        #create the multipolygon for the row
        multipolygon = convert_multipolygon(row[1])
        #get the blockgroup from the row
        blockgroup = row[2]
        print(blockgroup)
        #find out if the endpoints are in the blockgroup
        for col in ['from_blockgroup', 'to_blockgroup']:
            sewage_locations[col] = sewage_locations[col].\
                apply(lambda x: pt_in_poly(x, multipolygon, blockgroup))

    sewage_locations.to_csv('locations_with_endpoint_blockgroups_prelim.csv')

def pt_in_poly(pt_str, multipolygon, blockgroup):
    '''
    finds out if a point is in a blockgroup

    inputs:
        pt_str: (string) the point we are looking at
        multipolygon: a polygon shape representing the blockgroup
            that might contain the point depicted in pt_str
        blockgroup: the number of the blockgroup

    Outputs: if the point is in the blockgroup, returns blockgroup, if not,
        returns pt_str
    '''
    #if pt_str is a string we haven't found the blockgroup yet
    if isinstance(pt_str, str) and pt_str[0] == '[':
        point = create_point(pt_str) #create the point
        if point.within(multipolygon):
            #if the point is within the blockgroup, we record the blockgroup
            return(blockgroup)
        else:
            return(pt_str)
    else:
        return(pt_str)
