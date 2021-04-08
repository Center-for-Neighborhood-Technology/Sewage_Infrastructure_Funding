'''
Author: Esther Edith Spurlock

Title: Scrape Sewage Data

Organization: Center for Neighborhood Technology

Purpose: Scrape information off publicly avialbe PDF documents to indicate
    where funding has been allocated for sewage remodels and updates.

Code Inspirations:
    PDF Scraper: https://stackoverflow.com/questions/22898145/how-to-extract-text-and-text-coordinates-from-a-pdf-file
'''
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
from datetime import datetime
import gc
import math
import scraper_helper_functions as shf

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

def main(filepath, start_page, end_page, to_del, fix_wrap, start_str):
    '''
    The main of the file. Goes through the entire PDF scraping and analysis 
    process

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
        start_str: a string that the project number starts with for the
            given PDF

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
    scrape_PDF(filepath, start_page, end_page, to_del, fix_wrap, start_str)

    #turns our three dfs into Pandas dfs
    details_df = pd.DataFrame(data=DETAILS_DF).drop_duplicates()
    #del(DETAILS_DF)
    funding_df = pd.DataFrame(data=FUNDING_DF).drop_duplicates()
    #del(FUNDING_DF)
    location_df = pd.DataFrame(data=LOCATION_DF).drop_duplicates()
    #del(LOCATION_DF)

    return(details_df, funding_df, location_df)

    #return(df)

def scrape_PDF(filepath, start_page, end_page, to_del, fix_wrap, start_str):
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
        start_str: a string that the project number starts with for the
            given PDF

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
            #extract text from the object
            df = parse_object(layout._objs, df, start_str) 
            df = pd.DataFrame(data=df)  #turn df into a Pandas df
            
            #return(df)
            #identifies which projects are associated with whcih text
            in_2015 = "2015-2019" in filepath #are we in 2015-2019?
            in_2014 = "2014-2018" in filepath #are we in 2014-2018?
            df = shf.identify_project_id(df, in_2015, start_str)
            #return(df)
            #puts the test into the appropriate df
            categorize_text(df, to_del, fix_wrap, in_2015, in_2014, start_str)
            del df  #delete the dataframe

def parse_object(layout_objects, df, start_str):
    '''
    Gets text from objects on a PDF

    I got most of this code from the link listed as PDF Scraper listed in Code 
        Inspirations at the top of this document

    Inputs: layout_objects: objects from a PDF that need to be scraped
        df: a dataframe where we will store the scraped text from the document
        start_str: a string that the project number starts with for the
            given PDF

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
                    if text.startswith(start_str) \
                        and any(c.isalpha() for c in text):
                        lst = text.split() #split the list on whitespaces
                        for item in [' '.join(lst[:3]), ' '.join(lst[3:])]:
                            df = shf.add_scraped_to_df(df, x, y, item, index)
                    else:
                        df = shf.add_scraped_to_df(df, x, y, text, index)
        #if the instance is a container, then we use recursion
        elif isinstance(obj, pdfminer.layout.LTFigure):
            df = parse_object(obj._objs, df, start_str)

    return(df)

def categorize_text(df, to_delete, fix_wrap, in_2015, in_2014, start_str):
    '''
    Takes a dataframe and determines what type of data the text refers to and 
        then sends it off to be placed in the appropriate dataset

    Inputs:
        df: a pandas dataframe with our scraped information
        to_delete: a list of the strings that we want to delete
        fix_wrap: a list of project numbers 
            for the 2016 PDF: these have project titles that
                wrap around to a 2nd line
            for the 2015 PDF: these have project numbers where the Y values
                need to be readjusted before we round the Y value
        in_2015: (boolean) indicates if we are in the 2015 PDF or not
        in_2014: (boolean) indicates if we are in the 2014 PDF or not
        start_str: a string that the project number starts with for the
            given PDF

    Outputs: this does not output anything, but instead adds project
        information to the datasets regarding project details, project funding,
        and project location
    '''

    #first, we are going to delete text we know we do not want, as listed in
    #the to_delete list
    df = df[~df['Text'].isin(to_delete)]
    df = df[~df['Text'].str.startswith('Totals')]
    #now we will delete any of the lines that begin with "Totals"

    #round the X and Y values so they are easier to use
    if in_2015:
        #first, adjust some vaues depending on their project number
        df['Y'] = list(zip(df['Y'], df['Project_Number']))
        df['Y'] = df['Y'].apply(lambda x: x[0] + 0.11 if x[1] in fix_wrap \
            else x[0])
        df['Y'] = df['Y'].apply(lambda x: math.floor(x))
    else:
        df['Y'] = df['Y'].apply(lambda x: round(x, 1))
    df['X'] = df['X'].apply(lambda x: round(x, 3))
    #look to see if text contains spaces for future use
    df['Contains_Spaces'] = df['Text'].apply(lambda x: 1 if " " in x else 0)
    #look to see if text contains letters for future use
    df['Contains_Letters'] = df['Text'].apply(lambda x: 1 if any(c.isalpha()\
        for c in x) else 0)
    
    #gets a list of all the project numbers
    proj_nums = df['Project_Number'].unique().tolist()

    #if we are in the 2014 document, we need to categorize things differenely
    if in_2014:
        df = shf.categorize_2014(df, fix_wrap, start_str)

    #loop through the project numbers and create a df for each of the entries
    #associated with a project number
    for proj in proj_nums:
        this_proj_df = df.loc[df['Project_Number'] == proj]
        
        if in_2014:
            for item in ['details', 'funding', 'location']:
                this_item_df = this_proj_df\
                    .loc[this_proj_df['Categorize_Lst']==item].sort_values\
                    (by='X', ascending = True)
                if item == 'details':
                    project_details_add(this_item_df, proj, start_str,\
                       in_2015, in_2014)
                elif item == 'funding':
                    project_funding_add(this_item_df, proj, in_2014)
                elif item == 'location':
                    project_location_add(this_item_df, proj)
        else:
            #create a list of y values we can split the data on
            y_vals = this_proj_df['Y'].unique().tolist()
            if proj in fix_wrap and not in_2015:
                this_proj_df = shf.fix_wraparound(this_proj_df, proj)
            for y in y_vals:
                #creates a new df for the different values of y and sorts by x
                this_y_df = this_proj_df.loc[this_proj_df['Y'] == y]\
                    .sort_values(by='X', ascending = True)
                if proj in this_y_df['Text'].values:
                    #if the project number is in the dataframe, we know this is
                    #where the project dtails are
                    project_details_add(this_y_df, proj, start_str,\
                        in_2015, in_2014)
                else:
                    #if this is not the project details, we differentiate
                    #between funding and location by seeing if there are spaces
                    if 1 in this_y_df['Contains_Spaces'].values:
                        #if the strings in this dataframe contain spaces,
                        #they are locations
                        project_location_add(this_y_df, proj)
                    else:
                        #now we will see if any of the entires contains a 
                        #letter if one or more of the entries contains a 
                        #letter, we know this includes a funding source and 
                        #will include the data if none of the entries contain
                        #a letter, then we will not use the data
                        if 1 in this_y_df['Contains_Letters'].values:
                            project_funding_add(this_y_df, proj, in_2014)
                #delete df we are no longer using
                del this_y_df
        #delete df we are no longer using
        del this_proj_df

def project_details_add(df, project_num, start_str, in_2015, in_2014):
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
        start_str: a string that the project number starts with for the
            given PDF
        in_2015: (boolean) lets us know if we are in the 2015 PDF or not
        in_2014: (boolean) lets us know if we are in the 2014 PDF or not

    Outputs: this does not output anything, but instead adds project
        information to the project details dataset
    '''
    raw_details = df['Text'].tolist()

    #for the 2015 document, there are a few cases where a location sneaks
    #into the list at index 2, so we are removing it here
    if in_2015:
        if len(raw_details[2]) > 6:
            txt = raw_details[2]
            new_df = df.loc[df['Text']==txt]
            project_location_add(new_df, project_num)
            del new_df
            raw_details = raw_details[0:2] + raw_details[3:]

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

    #We need to make sure that the items come in the correct order
    date_lst = []
    project_title = ''

    if in_2014:
        date_format = '%b-%Y'
    else:
        date_format = '%b-%y'

    for item in details:
        try:
            datetime.strptime(item, date_format)
            date_lst.append(item)
        except ValueError:
            if not item.startswith(start_str):
                project_title = item
    
    if len(date_lst) != 2:
        print("We have too many dates!")
        print(df)
    #finds which date comes first
    start_date, end_date = shf.check_dates(date_lst[0], date_lst[1],\
        date_format)
    
    #adds our project details to the dataframe
    DETAILS_DF["Project_#"].append(project_num)
    DETAILS_DF["Project_Title"].append(project_title)
    DETAILS_DF["Start_Date"].append(start_date)
    DETAILS_DF["End_Date"].append(end_date)

    #delete list we are no longer using
    del details

def project_funding_add(df, project_num, in_2014):
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
        in_2014: (boolean) indicates if we are in the 2014 document or not

    Outputs: this does not output anything, but instead adds project
        information to the project funding dataset
    '''
    #first, make sure the indices are appropriately labeled
    #gets the number of funding sources
    num_funding = df['Contains_Letters'].sum()

    #loop through the different X values
    x_vals = df['X'].unique().tolist()

    #if we are in the 2014 document and the number of funding sources is > 1
    #we need to delete the 4 entries with the lowest y values as this is the
    #totals row, which we are not recording
    if in_2014 and num_funding > 1:
        target_length = num_funding * 5
        #while the length of the df is > num_funding * 5
        while len(df['Text']) > target_length:
            #we delete the records for the minimum Y value
            min_y = df['Y'].min()
            df = df[~df['Y'].isin([min_y])]

    #while we still have indices that are too big
    #we will subtract the indices that are too big by 1 until all
    #indices are the appropriate size
    while df['Index'].max() >= num_funding:
        #!!!we are just trying this
        #!!!I need to figure out how to not hard code these values
        if in_2014 and project_num in ['170 02 / 39146', '170 06 / 39028',
                                       '170 04 / 39029']:
            df = df[~df['Index'].isin([1,2])]
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
            df['Index'] = df['Index'].apply(lambda x: x[0] - 1 if x[1]\
                and x[0] >= num_funding else x[0])
    
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
        #!!!We are just triyng this
        #!!!We need to find a way to not hard code these numbers
        if project_num == '170 02 / 37933':
            total_alloc = max(details[1], details[2])
            prev_alloc = min(details[1], details[2])
            details[1] = total_alloc
            details[2] = prev_alloc
        
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

#FIX_WRAP_2016 = ['[170 -02] 37916']
#FIX_2015 = ['[170 -02] 38786', '[170 -02] 38796', '[170 -02] 38885',
#            '[170 -02] 38891', '[170 -02] 39562']
#FIX_2015_REHAB = ['[170 -06] 37890']
#P15_19_START = '['
P14_START = '170 '
FIX_2014_PROJ = ['Albany Ave: 82nd St to 83rd St',
                 'E. 107th St. / Langley Ave. / Alley West',
                 'E 92nd St from Anthony to Essex',
                 'N. Leoti Av./N. Spokane Av./W. Devon Av.',
                 '2018 Various Projects (PC)',
                 "2018 - Sewer Main Cleaning & TV'ing",
                 '2018 - Sewer Main Lining']

FIX_FUNDING_TOTALS = ['170 02 / 39146', '170 06 / 39028', '170 04 / 39029']

FIX_Y_VALS = [('170 02 / 39146', 425),('170 06 / 39028', 185),
              ('170 04 / 39029', 452)]

#!!!I need to fix the code so that I can just pass it in this list
#!!!instead of hard coding calues all over the place
FIX_2014 = [FIX_2014_PROJ, FIX_FUNDING_TOTALS, FIX_Y_VALS]

TO_DEL = ["(20)", "Project #      Project Title", "Design/",
             "Construction", "Start  End", "Year",
             "Fund", "Source", "2016 2020", "Allocation", "2015 2019",
             "2017 2021", "2018 2022", "2019 2023"]

#ex_full_pdf = "pdf_documents/2014-2018_cip.pdf"

#d, f, l = main(ex_full_pdf, 119, 122, TO_DEL, FIX_2014_PROJ, P14_START)
#d.to_csv('scraped_data/older/2014-2018_Sewer_Lining_Project_Details.csv')
#f.to_csv('scraped_data/older/2014-2018_Sewer_Lining_Funding.csv')
#l.to_csv('scraped_data/older/2014-2018_Sewer_Lining_Locations.csv')

#gc.collect()
