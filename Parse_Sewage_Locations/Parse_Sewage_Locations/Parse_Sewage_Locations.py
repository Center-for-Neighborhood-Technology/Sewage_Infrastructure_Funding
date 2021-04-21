'''
Author: Esther Edith Spurlock

Title: Parse Sewage Locations

Organization: Center for Neighborhood Technology

Purpose: Determine the latitude and ongitude of the endpoints associated with
    a location
'''

import psycopg2
import pandas as pd
import re
import geocoder
from helper_functions import make_connection, select_data

#!!!Question to answer: if we just have a single point, how are we going
#!!!to translate that into distance?

def main():
    '''
    Prepares our data for geospatial analysis by doing the following:
    
    1: Pulls in our data from our PostgreSQL database
    2: Splits up location name into beginning and end points
    3: Finds the latitude and longitude of each location point
    4: Saves data to CSV for geospatial analysis
    '''
    #connect to the postgresql database
    connection = make_connection()
    print("Connection made!")
    #create your cursor
    cursor = connection.cursor()
    data = select_data(cursor, 'project_locations')
    connection.close() #close the connection
    if data is not None:
        print("Data Retrieved!")
        #turn the data into a pandas df
        colnames = ['project_number', 'location_name', 'year_range']
        df = pd.DataFrame(data, columns=colnames)
        
        #create columns to hold where we are coming from and where we
        #are going to
        df['from'],df['to']=zip(*df['location_name'].apply(parse_locations))
        print("Locations Parsed!")

        #now we get the latitude and longitude of the endpoints
        for col in ['from', 'to']:
            print("Geocoding " + col)
            new_col_latln = col + '_lat_long'
            new_col_qual = col + '_quality'
            df[new_col_latln],df[new_col_qual] = df[col].apply(get_lat_long)
            print(col + " geocoded!")
    
        #save data in csv for use at a later time
        #!!!Note: there were some locations where the API did not pull in the
        #!!!latitude and longitude. I have gone in to enter those by hand
        df.to_csv('locations_with_lat_long.csv')
        #return(df)

    else:
        print("We received no data")

def parse_locations(location):
    '''
    Takes location data and splits it apart into the following elements:
        From: the point we are coming from
        To: The point we are going to

    Inputs: location: (string) the location we want to split apart

    Outputs: from_to: a list with the elements we want to split apart
    '''
    #case 1: AND two streets together to indicate a single point
    if ' And ' in location:
        return([location, None])
    #case 2: ' - ' the location name followed by the location address
    elif ' - ' in location:
        return([location.split(' - ')[1], None])
    ##case 3: ON FROM TO three streets together to indicate two points
        #connected to create a line
    elif location.startswith('On '):
        pieces_lst = re.split('On | From | To ', location)
        through_st = pieces_lst[1]
        from_loc = create_to_from(through_st, pieces_lst[2])
        to_loc = create_to_from(through_st, pieces_lst[3])
        return([from_loc, to_loc])
    #case 4: '#-#' two numbers connected by a dash with a through street
        #to indicate a street going from one number to another
    elif '-' in location:
        pieces_lst = location.split(' ', 1)
        through_st = pieces_lst[1]
        from_num, to_num = pieces_lst[0].split('-')
        from_loc = ' '.join([from_num, through_st])
        #we are coding 0 st as State St
        if to_num == '0':
            to_loc = ' '.join([through_st, 'And', 'State St'])
        else:
            to_loc = ' '.join([to_num, through_st])
        return([from_loc, to_loc])
    #case 5: a single address with no easy string indicators
    else:
        return([location, None])

def create_to_from(through_st, second_st):
    '''
    Creates a location point based on the through street and the content
        of the 2nd street

    Inputs:
        through_st: (string) the street that is used in both the to and from
            streets
        second_st: (string) either a to or a from st that we are merging with
            the through_st

    Outputs: (string) a location point
    '''
    #first, split the string by spaces so we can see the final "word"
    final_word = second_st.split(' ')[-1]
    if final_word.isnumeric():
        #If the final word is numeric, we will put it before the through_st
        return(' '.join([final_word, through_st]))
    else:
        #if a word is not numeric, the location point is a street cross section
        return(' '.join([through_st, 'And', second_st]))
    

def get_lat_long(address):
    '''
    Find the latitude and longitude of a point

    Inputs:
        address: a Chicago address we want the lat and long for

    Outputs: a tuple with the lat and long
    '''
    #!!!whoever is running this code will have to enter in their own API key
    api_key = 'Arkb2MGtDe7oesoWIjiTSfwYWQlJUe3dYMQFJNYe_FAD-2yo-ZfoHAoaqyy_23bZ'
    if address != None:
        #add the fact that we are in Chicago to make sure there are no errors
        address = address + ', Chicago, IL'
        location = geocoder.bing(address, key=api_key)
        return(location.latlng)
    else:
        return(None)

#main()

