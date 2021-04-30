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
    #we have already created a csv of our locations
    sewage_locations = pd.read_csv('unique_locations_w_endpoints.csv')\
        .fillna('None')
    #read in the csv with our lat and long for the endpoints
    lat_long = pd.read_csv('endpoints_w_correct_lat_long.csv')
    #now we fill in the lat and long
    for col in ['from', 'to']:
        new_col = col + '_lat_long'
        sewage_locations[new_col] = sewage_locations[col].\
            apply(lambda x: lat_long.\
            loc[lat_long['all_locations'] == x, 'lat_long'].iloc[0])

    #now we need to delete the records where we did not have a lat and long
    sewage_locations = sewage_locations.\
        loc[~sewage_locations[['from_lat_long', 'to_lat_long']].\
        isin(['[]']).any(axis=1)]
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

    sewage_locations.to_csv('unique_locations_with_endpoint_blockgroups.csv')

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

