The code written here takes PDF documents and scrapes information from them about sewage infrastructure
funding.

Scrape_Sewage_Data.py: the code that takes a PDF document, scrapes it for information, and returns
	the scraped data in pdfs

PDF_documents: a file folder that holds the PDF documents we want to scrape

scraped_data: a file folder that holds the scraped data
	for each PDF, we have 3 csv files in this folder with the following information
	details:
		project #
		project title
		start date
		end date
	funding:
		project #
		funding source
		total allocation
		allocation from previous year
		current year allocation
		alocation for 4 years
	locations:
		project #
		project location
