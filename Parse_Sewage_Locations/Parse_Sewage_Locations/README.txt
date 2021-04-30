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
endpoints_w_correct_lat_long: Individual beginning or ending points that have the correct latitude
	and longitude. Some of the entries are using the Bing api and some use the mapquest api. Also,
	for some of these, I have entered in the information by hand. I also have included those locations
	that do not have a lat/long and have indicated that they don't have coordinates with '[]'. I
	created this csv in iPython3 and excel.
locations_endpoints_no_latlon: this is a csv that I used to help find the lat/long for some points
	that did not have lat/long. I took a full location and tried to find the lat/long by seeing
	what was around one of the endpoints. I was not able to find all of the endpoint lat/longs. I
	have kept this csv here because if there is any question about the quality of the lat/longs I found,
	you can use this to see which locations I used this technique on.
locations_errors: this is a csv created by the Find_Lengh py file. It indicates which records had an
	error when we tried to find the distances in the block groups.
locations_w_long_distance: at one point, the Find_Length py file also kept track of which locations
	had a long distance. I then used this information to error check if the endpoints were correct.
	I have kept this csv around so you can double check my work and see where there were errors
	previously.
locations_w_parsed_distances: this csv comes from the Find_Lengh py file. It is a list of all the
	unique locations and the length that they pass through each block group.
single_point_locations: this csv indicates which locations are merely at a single point and which
	block group that point is in
unique_locations_w_endpoints: this csv holds all the unique locations scraped from the PDFs and has
	split apart the beginning and ending points
unique_locations_with_endpoint_blockgroups: this adds to the Unique_locations_w_endpoints csv by including
	the lat/long for the endpoints and which blockgroup those endpoints are in.
