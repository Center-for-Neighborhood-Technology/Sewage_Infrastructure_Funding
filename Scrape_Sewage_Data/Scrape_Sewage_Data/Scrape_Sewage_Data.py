'''
Author: Esther Edith Spurlock

Title: Scrape Sewage Data

Organization: Center for Neighborhood Technology

Purpose: Scrape information off publicly avialbe PDF documents to indicate
    where funding has been allocated for sewage remodels and updates.

Code Inspirations:
    PDF Scraper: https://stackoverflow.com/questions/22898145/how-to-extract-text-and-text-coordinates-from-a-pdf-file
'''

#!!!In general, I need to remember to add garbage collection and deleteion to 
#!!!this code

#!!!On page 96/97, there is a project name that wraps around to a 2nd line
#!!!that is causing an error. I have implemented a hard-coded solution, but
#!!!I may want to come back to it

#import statements
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator
import pdfminer
import pandas as pd
import numpy as np
from datetime import datetime
import gc

#initializing the 3 dataframes that we will want to fill in by the end of this 
#process
DETAILS_DF = {"Project_#": [],
            "Project_Title": [],
            "Start_Date": [],
            "End_Date": []}
FUNDING_DF = {"Project_#": [],
              "Funding_Source": [],
              "Total_Allocation": [],
              "Allocation_From_Previous_Year": [],
              "Current_Year_Allocation": [],
              "Allocation_For_4_Years": []}

LOCATION_DF = {"Project_#": [],
               "Project_Location": []}

def main(filepath, start_page, end_page, to_del, fix_wrap):
    '''
    The main of the file. Goes through the entire PDF scraping and analysis 
    process

    !!! I need to fix this so it will NOT output a df, but will instead update 
    !!!the SQL database
    
    Inputs: filepath: (string) the path to the PDF we want to scrape
        start_page: the starting page we want to scrape
        end_page: the ending page we want to scrape
        The start page and end page are the pages according to the PDF 
            document, and not the page numbers as listed at the bottom of 
            the page.
        to_del: a list of strings that need to be deleted from the raw scraped
            data
        fix_wrap: a list of project numbers that have project titles that
            wrap around to a 2nd line

    Outputs: df: 
        details_df: a Pandas dataframe that has the scraped data from our PDF 
            about project details
        funding_df: a Pandas dataframe that has the scraped data from our PDF 
            about project funding 
        location_df: a Pandas dataframe that has the scraped data from our PDF 
            about project location
    '''
    start_page -= 1 #because pdfminer starts with 0 instead of 1 
        #(which would be on the PDF document) we need to subtract 1
        #we will not substract 1 from the end page because range does not 
        #include the last number
    scrape_PDF(filepath, start_page, end_page, to_del, fix_wrap)

    #turns our three dfs into Pandas dfs
    details_df = pd.DataFrame(data=DETAILS_DF).drop_duplicates()
    funding_df = pd.DataFrame(data=FUNDING_DF).drop_duplicates()
    location_df = pd.DataFrame(data=LOCATION_DF).drop_duplicates()

    #!!!Once I have all of the pages in, I will need to remove duplicates for 
    #!!!the few examples of projects that go onto multiple pages
    return(details_df, funding_df, location_df)

    #return(df)

def scrape_PDF(filepath, start_page, end_page, to_del, fix_wrap):
    '''
    Scrapes text from a PDF document

    I got most of this code from the link listed as PDF Scraper listed in Code
        Inspirations at the top of this document

    Inputs: 
        filepath: (string) the path to the PDF we want to scrape
        start_page: the starting page we want to scrape
        end_page: the ending page we want to scrape
        to_del: a list of strings that need to be deleted from the raw scraped
            data
        fix_wrap: a list of project numbers that have project titles that
            wrap around to a 2nd line

    Outputs: none, instead it puts data into datasets about project details,
        funding, and location
    '''
    file = open(filepath, 'rb') #open the PDF file
    parser = PDFParser(file) #create a PDF parser for the file
    #create a document that stores the document structure
    document = PDFDocument(parser) 

    #error handling: make sure the document allows for text extraction
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    resource_manager = PDFResourceManager() #create a resource manager
    device = PDFDevice(resource_manager) #create a PDF device object

    #here is where we begin our layout analysis
    laparams = LAParams() #set up parameters for analysis
    #change the device to be a PDF page aggregator object
    device = PDFPageAggregator(resource_manager, laparams=laparams) 
    #create a PDF interpreter object
    interpreter = PDFPageInterpreter(resource_manager, device) 

    #loop through all the pages of the document
    for page_num, page in enumerate(PDFPage.create_pages(document)):
        #make sure the page number we have is in the appropriate page range
        if page_num in range(start_page, end_page):
            #read the page into a layout object
            interpreter.process_page(page)
            layout = device.get_result()
            #creates an empty df for every page
            df = {'X': [],
                'Y': [],
                'Text': [],
                'Index': []}
            df = parse_object(layout._objs, df) #extract text from the object
            df = pd.DataFrame(data=df)  #turn df into a Pandas df
            
            #identifies which projects are associated with whcih text
            df = identify_project_id(df)
            #return(df)
            #puts the test into the appropriate df
            categorize_text(df, to_del, fix_wrap)
            del df  #delete the dataframe

def parse_object(layout_objects, df):
    '''
    Gets text from objects on a PDF

    I got most of this code from the link listed as PDF Scraper listed in Code 
        Inspirations at the top of this document

    Inputs: layout_objects: objects from a PDF that need to be scraped
        df: a dataframe where we will store the scraped text from the document

    Outputs: pdf_data_df: a dataframe that has the scraped data from our PDF
    '''
    for obj in layout_objects:
        #if the object is a textbox, then get the text and location
        if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
            #get the x and y values
            x, y = obj.bbox[0], obj.bbox[1]
            #get a list of the different text elements in this object
            txt_lst = obj.get_text().split('\n')
            #stores each element in the list in its own entry, keeping track
            #of which text came first
            for index, text in enumerate(txt_lst):
                if text != '': #we do not care about the empty string
                    #If we have a project number and project title in the same
                    #entry, we need to separate them
                    #!!!This includes some hardcoded values
                    if text.startswith('[') and any(c.isalpha() for c in text):
                        lst = text.split() #split the list on whitespaces
                        for item in [' '.join(lst[:3]), ' '.join(lst[3:])]:
                            df = add_scraped_to_df(df, x, y, item, index)
                    else:
                        df = add_scraped_to_df(df, x, y, text, index)
        #if the instance is a container, then we use recursion
        elif isinstance(obj, pdfminer.layout.LTFigure):
            df = parse_object(obj._objs, df)

    return(df)

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

def identify_project_id(df):
    '''
    Takes in a Pandas dataframe and adds a column that indicates if an entry
        belongs to a certain project or not

    Inputs: df: a pandas dataframe with the raw scraped text from the pdf

    Outputs: df: a pandas dataframe that indicats what project number 
        the scraped text belongs to
    '''
    #create a new df that is a subset of the old df with just the rows that
    #list the project numbers
    #!!! Right now I am hard coding in the fact that project numbers begin
    #!!!with a '[' because of how the document is written
    proj_num_df = df.loc[df['Text'].str[0] == '[']
    #We will make sure that the dataframe is sorted in descending order
    proj_num_df = proj_num_df.sort_values(by=['Y'], ascending=False)

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
    #!!!Again, we are hard coding in the project number because of the document
    #!!!we are currently working with
    df = df.loc[df['Project_Number'].str[0] == '[']
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

def categorize_text(df, to_delete, fix_wrap):
    '''
    Takes a dataframe and determines what type of data the text refers to and 
        then sends it off to be placed in the appropriate dataset

    Inputs:
        df: a pandas dataframe with our scraped information
        to_delete: a list of the strings that we want to delete
        fix_wrap: a list of project numbers that have project titles that
            wrap around to a 2nd line

    Outputs: this does not output anything, but instead adds project
        information to the datasets regarding project details, project funding,
        and project location
    '''

    #!!! For future pages/documents, we may need to add to the list of things
    #!!!that need deletion
    #!!! For future pages/documents, we may need to keep an eye out for the
    #!!!page number

    #first, we are going to delete text we know we do not want, as listed in
    #the to_delete list
    df = df[~df['Text'].isin(to_delete)]
    df = df[~df['Text'].str.startswith('Totals')]
    #now we will delete any of the lines that begin with "Totals"

    #round the X and Y values so they are easier to use
    df['Y'] = df['Y'].apply(lambda x: round(x, 1))
    df['X'] = df['X'].apply(lambda x: round(x, 3))
    #look to see if text contains spaces for future use
    df['Contains_Spaces'] = df['Text'].apply(lambda x: 1 if " " in x else 0)
    #look to see if text contains letters for future use
    df['Contains_Letters'] = df['Text'].apply(lambda x: 1 if any(c.isalpha()\
        for c in x) else 0)
    
    #gets a list of all the project numbers
    proj_nums = df['Project_Number'].unique().tolist()

    #loop through the project numbers and create a df for each of the entries
    #associated with a project number
    for proj in proj_nums:
        this_proj_df = df.loc[df['Project_Number'] == proj]
        #create a list of y values we can split the data on
        y_vals = this_proj_df['Y'].unique().tolist()
        #!!!We are hard coding in this value because for 2016-2020 it happens
        #!!!only once and we need to come up with a slicker way of dealing
        if proj in fix_wrap:
            this_proj_df = fix_wraparound(this_proj_df, proj)
        for y in y_vals:
            #creates a new df for the different values of y and ensures the x
            #is sorted in ascending order
            this_y_df = this_proj_df.loc[this_proj_df['Y'] == y].sort_values\
                (by='X', ascending = True)
            #next, we are going to sort the text in these different y groupings
            if proj in this_y_df['Text'].values:
                #if the project number is in the dataframe, we know this is
                #where the project dtails are
                project_details_add(this_y_df, proj)
            else:
                #if this is not the project details, we differentiate between
                #funding and location by seeing if there are spaces in the text
                if 1 in this_y_df['Contains_Spaces'].values:
                    #if the strings in this dataframe contain spaces, we know
                    #they are locations
                    project_location_add(this_y_df, proj)
                else:
                    #now we will see if any of the entires contains a letter
                    #if one or more of the entries contains a letter, we know
                    #this includes a funding source and will include the data
                    #if none of the entries contain a letter, then we will not
                    #use the data
                    if 1 in this_y_df['Contains_Letters'].values:
                        project_funding_add(this_y_df, proj)
            #delete df we are no longer using
            del this_y_df
        #delete df we are no longer using
        del this_proj_df

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

def project_details_add(df, project_num):
    '''
    Adds data to the project details dataframe

    Data added:
        Project #
        Project Title
        Start date
        End date

    Inputs:
        df: a pandas dataframe with information about the project details
        project_num: this project's project number

    Outputs: this does not output anything, but instead adds project
        information to the project details dataset
    '''
    raw_details = df['Text'].tolist()

    #here we will do error handling to ensure we are getting what we expect
    if len(raw_details) != 4:
        details_df = {}
        #if there are more than 4 values, then it means that the project
        #details are in the 1st 4 entries
        #and the remaining entries are funding based
        details = raw_details[:4]
        #create an entry for the funding source
        single_funding_source_add(raw_details[4:], project_num)
    else:
        details = raw_details

    #finds which date comes first
    start_date, end_date = check_dates(details[2], details[3])
    
    #adds our project details to the dataframe
    DETAILS_DF["Project_#"].append(details[0])
    DETAILS_DF["Project_Title"].append(details[1])
    DETAILS_DF["Start_Date"].append(start_date)
    DETAILS_DF["End_Date"].append(end_date)

    #delete list we are no longer using
    del details

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

def project_funding_add(df, project_num):
    '''
    Adds data to the project funding dataframe

    Data added:
        Project # (for each funding source)
        Funding source (might be > 1)
        Total allocation (for each funding source)
        Allocation from a previous year (for each funding source)
        Current year allocation (for each funding source)
        Allocation for full 4-year period (for each funding source)

    Inputs:
        df: a pandas dataframe with information about the project funding
        project_num: this project's project number

    Outputs: this does not output anything, but instead adds project
        information to the project funding dataset
    '''
    #first, make sure the indices are appropriately labeled
    #gets the number of funding sources
    num_funding = df['Contains_Letters'].sum()
    #loop through the different X values
    x_vals = df['X'].unique().tolist()
    #an empty list where we will store the x values that have indices that
    #are higher than the number of funding sources
    error_x_vals = []
    for x in x_vals:
        #creates a new df for the different values of x
        this_x_df = df.loc[df['X'] == x]
        #if the max value of the index for that x value > number of funding
        #sources, then we know there is an error with the indices
        if this_x_df['Index'].max() >= num_funding:
            error_x_vals.append(x)
        #delete df we are no longer using
        del this_x_df

    #creates a new column to indicate if the indices need to be changed
    if error_x_vals != []:
        df['Fix Index'] = df['X'].apply\
            (lambda x: True if x in error_x_vals else False)
        #creates a list in the index column so we can apply our lambda
        df['Index'] = list(zip(df['Index'], df['Fix Index']))
        #change the index
        #!!!we are hard coding in the subtract by 2 based on the document
        df['Index'] = df['Index'].apply(lambda x: x[0] - 2 if x[1]\
            else x[0])

    #split the df apart by indices
    indices = df['Index'].unique().tolist()
    for i in indices:
        #creates a new df for the different indices and ensures the x is sorted
        #in ascending order
        this_index_df = df.loc[df['Index'] == i].sort_values\
            (by='X', ascending = True)
        details = this_index_df['Text'].tolist()
        #here we will do error handling to ensure we are getting what we expect
        if len(details) != 5:
            print("This project funding dataframe is the wrong length! (one)")
            print(project_num)
            print(df)
        else:
            single_funding_source_add(details, project_num)
        #delete df we are no longer using
        del this_index_df

def single_funding_source_add(details, project_num):
    '''
    Takes a single funding source and adds the data to a dataframe

    Data added:
        Project # (for each funding source)
        Funding source (might be > 1)
        Total allocation (for each funding source)
        Allocation from a previous year (for each funding source)
        Current year allocation (for each funding source)
        Allocation for full 4-year period (for each funding source)

    Inputs:
        details: a list with information about the project details
        project_num: this project's project number

    Outputs: this does not output anything, but instead adds project
        information to the project details dataset
    '''
    #here we will do error handling to ensure we are getting what we expect
    if len(details) != 5:
        print("This project funding dataframe is the wrong length! (two)")
        print(project_num)
        print(details)

    #puts the funding data into the dataframe
    else:
        FUNDING_DF["Project_#"].append(project_num)
        FUNDING_DF["Funding_Source"].append(details[0])
        FUNDING_DF["Total_Allocation"].append(details[1])
        FUNDING_DF["Allocation_From_Previous_Year"].append(details[2])
        FUNDING_DF["Current_Year_Allocation"].append(details[3])
        FUNDING_DF["Allocation_For_4_Years"].append(details[4])

def project_location_add(df, project_num):
    '''
    Adds data to the project location dataframe

    Data added:
        Project # (for each location)
        Project location (probably will be > 1)

    Inputs:
        df: a pandas dataframe with information about the project location
        project_num: this project's project number

    Outputs: this does not output anything, but instead adds project
        information to the project location dataset
    '''
    #create an empty df where we can store our location data
    
    #grabs out the different locations
    locations = df['Text'].tolist()

    for loc in locations:
        LOCATION_DF["Project_Location"].append(loc)
        LOCATION_DF["Project_#"].append(project_num)

FIX_WRAP_2016 = ['[170 -02] 37916']
TO_DEL = ["(20)", "Project #      Project Title", "Design/",
             "Construction", "Start  End",
             "Fund", "Source", "2016 2020", "Allocation", "2015 2019"]


ex_full_pdf = "pdf_documents/2016-2020_cip.pdf"
start = 95
end = 106

d, f, l = main(ex_full_pdf, start, end, TO_DEL, FIX_WRAP_2016)
d.to_csv('scraped_data/2016-2020_Sewer_System_Replacement_' +
        'Construction_Project_Details.csv')
f.to_csv('scraped_data/2016-2020_Sewer_System_Replacement_' +
         'Construction_Funding.csv')
l.to_csv('scraped_data/2016-2020_Sewer_System_Replacement_' +
         'Construction_Locations.csv')

gc.collect()
