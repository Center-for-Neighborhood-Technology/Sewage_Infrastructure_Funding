'''
Author: Esther Edith Spurlock

Title: Scrape Sewage Data

Organization: Center for Neighborhood Technology

Purpose: Aid in PDF scraping
'''

import pandas as pd
from datetime import datetime

def add_scraped_to_df(df, x, y, text, index):
    '''
    Adds scraped information to the dataframe

    Inputs:
        df: the dataframe where we are storing our scraped data
        x: (float) the x-coordinate of the text
        y: (float) the y-coordinate of the text
        text: (string) the text that has been scraped from the PDF
        index: (int) the index of where this text appeared in the text box

    Outputs: df: the updated dataframe
    '''
    df['X'].append(x)
    df['Y'].append(y)
    df['Text'].append(text.strip())
    df['Index'].append(index)
    return(df)

def identify_project_id(df, in_2015, start_str):
    '''
    Takes in a Pandas dataframe and adds a column that indicates if an entry
        belongs to a certain project or not

    Inputs: 
        df: a pandas dataframe with the raw scraped text from the pdf
        in_2015: (boolean) indicates if we are in the 2015 PDF or not
        start_str: a string that the project number starts with for the
            given PDF

    Outputs: df: a pandas dataframe that indicats what project number 
        the scraped text belongs to
    '''
    #create a new df that is a subset of the old df with just the rows that
    #list the project numbers
    proj_num_df = df.loc[df['Text'].str.startswith(start_str)]
    #We will make sure that the dataframe is sorted in descending order
    proj_num_df = proj_num_df.sort_values(by=['Y'], ascending=False)

    #if we are in the 2015-2019 document, we need to readjust our Y values
    #because in the 2015-2019 PDF, some Y values we want are higher than
    #the project number Y value
    if in_2015:
        proj_num_df['Y'] = proj_num_df['Y'].apply(lambda x: x + 0.1)

    all_y = proj_num_df['Y'].tolist() #get a list of all the y values
    all_lowest_y = [] #an empty list where to store the values of the lowest y
    num_projs = len(all_y) #the number of projects there are
    
    #loop through the number of projects
    for x in range(num_projs):
        next = x + 1 #the index of the next y value
        if next == num_projs:
            #puts in 0 for the lowest y value of the last project
            all_lowest_y.append(0)
        else:
            #puts in the y value for the next project number
            all_lowest_y.append(all_y[next])

    #creates a new column in the df for the lowest y values
    proj_num_df.loc[:, 'Lowest_Y'] = all_lowest_y

    #creates a column that will eventually hold the project number
    #because we calculate the project number from the y value, we initialize 
    #the column to be the y value
    #in order to ensure we get all of the data, we will round the y value to
    #the 2nd decimal place
    df['Project_Number'] = df['Y'].apply(lambda x: round(x, 2))

    #loops through the projects
    for index, row in proj_num_df.iterrows():
        #pulls out the y values we care about and the project number
        greatest_y, proj_num, lowest_y = row[1], row[2], row[4]
        #changes the project number column to indicate what project number the
        #text is associated with
        df['Project_Number'] = df['Project_Number'].apply(lambda x: proj_num\
            if in_range(x, greatest_y, lowest_y) else x)
    
    #we just want the rows that have a project number
    df['Project_Number'] = df['Project_Number'].apply(lambda x: str(x))
    df = df.loc[df['Project_Number'].str.startswith(start_str)]
    return(df)

def in_range(check, high, low):
    '''
    Checks if a float is between two other floats

    Inputs:
        check: (float) the number we want to check
        high: (float) the highest number in our range
        low: (float) the lowest number in our range

    Outputs: a boolean indicating if the number to check is in range
    '''
    if type(check) == str:
        #First, we need to make sure the value we are checking is not a string
        return(False)
    elif (check <= high) & (check > low):
        return(True)
    else:
        return(False)

def fix_wraparound(this_proj_df, proj):
    '''
    When we have a project title that wraps to a 2nd line, it causes an error
    In this code, we fix the df associated with that project

    Inputs: this_proj_df: the dataframe that holds the wraparound error
        proj: the project number for this df

    Outputs: this_proj_df: the fixed dataframe
    '''
    #we find the y value that occurs the least
    y_to_fix = this_proj_df['Y'].value_counts().argmin()
    y_to_fix_df = this_proj_df.loc[this_proj_df['Y'] == y_to_fix]
    new_text_lst = y_to_fix_df['Text'].tolist()
    new_text = ' '.join(new_text_lst)
    new_x = y_to_fix_df['X'].min()
    #the y value needs to be the same as the project number y value
    new_y = this_proj_df['Y'].\
        loc[this_proj_df['Text']==proj].tolist()[0]
    #create a new dataframe with our updated information
    new_data = {'X': [new_x],
                    'Y': [new_y],
                    'Text': [new_text],
                    'Index': [0],
                    'Project_Number': [proj],
                    'Contains_Spaces': [1],
                    'Contains_Letters': [1]}
    to_add_df = pd.DataFrame(data=new_data)
    #add the new data to this project's dataframe
    this_proj_df = this_proj_df.append(to_add_df)
    #delete the entries for the y values we don't want
    this_proj_df = this_proj_df[~this_proj_df['Y'].isin([y_to_fix])]
    #delete the intermediate data
    del new_data
    del to_add_df
    return(this_proj_df)

def check_dates(date1, date2):
    '''
    Takes a start date and an end date and determines which comes first

    Inputs:
        date1: a string with one of the dates
        date2: a string with another of the dates

    Outputs:
        date1 and date2 in chronological order
    '''
    date_format = '%b-%y'   #this is the format that the dates will be given
    #check which date comes first and returns it in the appropriate order
    if datetime.strptime(date1, date_format) < \
        datetime.strptime(date2, date_format):
        return(date1, date2)
    else:
        return(date2, date1)

def categorize_2014(df, proj_nums, start_str):
    '''
    Takes scraped data from the 2014-2018 PDF and indicates which dataset they
    should end up in

    !!!inputs and outputs to come later
    '''
    proj_num_df = df.loc[df['Text'].str.startswith(start_str)]
    y_lst = proj_num_df['Y'].tolist()
    #change 'Contains_Letters' and 'Contains_Spaces' to be true or false
    for col in ['Contains_Spaces', 'Contains_Letters']:
        df[col] = df[col].apply(lambda x: x == 1)
    #create a column indicating if the y value is the same as a project
    #number's y value
    df['Beginning_Y'] = df['Y'].apply(lambda x: x in y_lst)
    #create a column that indicates if there is a dash
    df['Has_Dash'] = df['Text'].apply(lambda x: '-' in x)
    #create a column that is a list of the three things we will use to
    #identify what dataset everything should go in
    df['Categorize_Lst'] = list(zip(df['Contains_Spaces'], \
       df['Contains_Letters'], df['Beginning_Y'], df['Has_Dash']))
    df['Categorize_Lst']=df['Categorize_Lst']\
        .apply(lambda x: categorize(x))
    return(df)

def categorize(cat_lst):
    '''
    Categorizes which dataset a single entry should be in

    !!!Inputs and outputs to come later
    '''
    contains_spaces, contains_letters, beginning_y, has_dash = cat_lst
    if beginning_y:
        return('details')
    elif has_dash and not contains_spaces:
        return('details')
    elif not contains_spaces and not contains_letters:
        return('funding')
    elif not has_dash and not contains_spaces and contains_letters:
        return('funding')
    else:
        return('location')

