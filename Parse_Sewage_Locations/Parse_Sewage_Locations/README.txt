These files take the locations data we have scraped from PDFs and finds out which block groups
each location passes through and the length that each location is in each block group.

Python Files:
Find_Blockgroups: finds which block group a beginning or ending point is in
Find_Length: Finds the length a location is in a given block group
Parse_Sewage_Locations: Breaks apart location information into beginning and ending points and
	finds out the latitude and longitude of those points
helper_functions: functions that can be used in any file and help support the functionality
	of the other Python files

In order to save runtime, I have saved my intermittent steps into the following CSVs:
blkgrps_2019_clipped: a CSV downloaded from PostgreSQL database. Contains the block group number
	and the multipolygon information associated with that block group.
locations_with_lat_long: the output of Parse_Sewage_Locations. Contains the location endpoints
	and the latitude and longitude of those points
locations_with_endpoint_blockgroups_prelim: adds onto the locations_with_lat_long CSV by adding
	which block group the end point is in