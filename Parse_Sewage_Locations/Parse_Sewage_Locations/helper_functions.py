'''
Author: Esther Edith Spurlock

Title: Helper Functions

Organization: Center for Neighborhood Technology

Purpose: Functions that are used to aid in the running of other modules
'''

import psycopg2
from shapely.geometry import Point, Polygon

def make_connection():
    '''
    Connect to the postgresql database

    Inputs: none

    Outputs: connection: a connection to the postgresql database
    '''
    connected = False
    while not connected:
        #get the password from the user
        pwd = input("Please enter the database password: ")
        try:
            #if the password is correct, we connect to the database
            connection = psycopg2.connect(
                host = "prod4.cubs2ve1iiap.us-east-1.rds.amazonaws.com",
                database = "cook_county",
                user = "intern",
                password = pwd)
            connected = True
            return(connection)
        except (Exception, psycopg2.DatabaseError) as error:
            #if the password is incorrect, we stay in our loop
            print(error)
            print("Connection not made")

def select_data(cursor, table_name):
    '''
    Returns desired data from our postgresql database

    Inputs: 
        cursor: a cursor for our postgresql database
        table_name: (string) the table we want to get data from

    Outputs: data: our desired data
    '''
    selection_query = """SELECT * """ + \
        """FROM cook_county.chicago_sewer_study.""" + table_name +\
        """;"""
    try:
        #attempt to execute the selection query
        cursor.execute(selection_query)
        #fetch the data returned by the selection
        data = cursor.fetchall()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        data = None
    
    cursor.close() #close the cursor
    return(data)

def convert_multipolygon(multi_str):
    '''
    Converts a string with multipolygon information into a multipolygon object

    Inputs: multi_str: a string of the multipolygon vertices

    Outputs: a Polygon object
    '''
    #take off the beginning and ending substrings
    multi_str = multi_str.replace('MULTIPOLYGON (((','').strip(')')
    #split apart on the comma
    multi_str = multi_str.split(', ')
    #create an empty list to store coordinates
    coord_lst = []
    #put the coordinates of the latitude and longitude into the coordinate list
    for lat_ln in multi_str:
        ln, lat = lat_ln.strip(')').strip('(').split(' ')
        coord_lst.append((float(lat),float(ln)))

    #create a polygon and return it
    return(Polygon(coord_lst))

def create_point(pt_str):
    '''
    Converts a string with latitude and longitude into a point object

    Inputs: pt_str: a string with the latitude and longitude of our points

    Outputs: a Point object
    '''
    return(Point(get_floats(pt_str)))

def get_floats(pt_str):
    '''
    Converts a string with latitude and longitude information into a tuple
    of two floats

    Inputs: pt_str: a string with the latitude and longitude of our points

    Outputs: a tuple with latitude and longitude information
    '''
    #if we have a 'None' value, just return it back
    if pt_str == 'None':
        return(pt_str)
    #take off the beginning and ending substrings
    pt_str = pt_str.replace('[','').replace(']','')
    #split apart on the comma
    lat, ln = pt_str.split(', ')
    #create a point and return it
    return((float(lat),float(ln)))

def get_id(blockgroup_id):
    '''
    Takes a string and returns the blockgorup ID as an int or returns the
    string back to you if there is no blockgroup id

    inputs: blockgroup_id: (string) the id you want to convert

    outputs: the converted blockgroup id with a boolean indicating if there
        is a blockgroup id or not
    '''
    if blockgroup_id.startswith('[') or blockgroup_id == 'None':
        return(blockgroup_id, False)
    else:
        return(int(blockgroup_id), True)
