'''
After we have finished with the main portion of the data there are 2 things
we need to take care of:

#before we begin coding, we need to exclude the ~100 entries that we do not
#have the block group for either the beginning or the ending point.
#the current hypothesis is that these locations touch a block point
#this is already saved in a csv

#we also need to deal with the error locations (as per the quality dataframe)
#there are 227 entries for these

#we also need to deal with the locations that struggled with finding the
#intersection in a blockgroup
#I have these entries saved in 2 csvs

#another thing we need to keep in mind is that there are some project titles
#that have location information (but there were no locations associated
#with the project) We are, similarly, going to save these until after we have
#finished everything here
'''
