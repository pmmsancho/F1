#%% 0. Intro

# =============================================================================
# 0.1 Clearing and packages
# =============================================================================

# Clearing
%reset -f

# Packages
import requests
import lxml.html as lh
import pandas as pd
import numpy as np
import pickle

# Setting of warning
pd.options.mode.chained_assignment = None  

#%% 1. Webscraping

# =============================================================================
# 1.1 Storing track and time information
# =============================================================================

# URL names of the different tracks (taken from 2018)
tracks = {'australia' : 'australie',
          'bahrain' : 'bahrein',
          'china' : 'chine',
          'azerbaijan' : 'azerbaidjan',
          'spain' : 'espagne',
          'monaco' : 'monaco',
          'canada' : 'canada',
          'france' : 'france',
          'austria' : 'autriche',
          'uk' : 'grande-bretagne',
          'germany' : 'allemagne',
          'hungary' : 'hongrie',
          'belgium' : 'belgique',
          'italy' : 'italie',
          'singapur' : 'singapour',
          'russia' : 'russie',
          'japan' : 'japon',
          'usa' : 'etats-unis',
          'mexico' : 'mexique',
          'brasil' : 'bresil',
          'abudhabi' : 'abou-dhabi'
          }

# Applied years
years = ['2009',
         '2010',
         '2011',
         '2012',
         '2013',
         '2014',
         '2015',
         '2016',
         '2017',
         '2018',
         '2019'
         ]

# =============================================================================
# 1.2 Scrape Rows of the table
# =============================================================================

# Initiation of a session number
session_number = 0

for track in tracks:
    for year in years:
                
        # Relevant URL
        url = 'https://www.statsf1.com/en/' + year + '/' + tracks[track] + '/qualification.aspx'

        # Generating a new session number
        session_number+=1

        # Using a proxy IP adress
        payload = {'api_key': 'CODE HAS TO BE INSERTED ',
                   'url': url,
                   'session_number' : str(session_number)}

        # Create a handle page, to handle the contents of the website
        page = requests.get('http://api.scraperapi.com', params=payload)

        # Store the contents of the website under doc
        doc = lh.fromstring(page.content)

        # Parse data that are stored between <tr>..</tr> of HTML
        tr_elements = doc.xpath('//tr')

        # Checking now whether all rows have the same width
        [len(T) for T in tr_elements[:12]] # All the same

# =============================================================================
# 1.3 Creating header through first row
# =============================================================================
        
        # Create empty list
        col = []
        i = 0
        
        if len(tr_elements) > 0:
        
            # For each row, store each first element (header) and an empty list
            for t in tr_elements[0]:
                i+=1
                name = t.text_content()
                col.append((name,[]))
                
# =============================================================================
# 1.4 Creating extracting the information from each row
# =============================================================================
        
            # Since the first row is the header, data is stored on the second row onwards
            
            for j in range(1,len(tr_elements)):
                # T is our j'th row
                T = tr_elements[j]
                
                # If row is not of size 8, the //tr data is not from our table
                if len(T) != 8:
                    break
                
                # i is the index of our column
                i = 0
                
                # Iterate through each element of the row
                for t in T.iterchildren():
                    data = t.text_content()
                    # Check if row is empty
                    if i > 0:
                        #Convert any numerical value to integers
                        try: 
                            data = int(data)
                        except:
                            pass
                    # Append the data to the empty list of the i'th column
                    col[i][1].append(data)
                    # Increment i for the next column
                    i+=1
                    
                # Just to make sure that each column has the same length
                [len(C) for (title,C) in col] # All the same
        
# =============================================================================
# 1.5 Creating a dataframe with that information
# =============================================================================
        
                Dict = {title:column for (title,column) in col}
                globals()[track + '_' + year] = pd.DataFrame(Dict)


#%% 2. Changing data format & saving

# =============================================================================
# 2.1 Appending all data
# =============================================================================

# Getting column names from a random track and using the fact that they are all the same
columns = abudhabi_2009.columns

# Empty Container
qualification = pd.DataFrame(columns = columns)

for track in tracks:
    for year in years:
        try:
            # Adding track location name 
            eval(track + '_' + year)['track'] = Track 
            
            # Adding year information
            eval(track + '_' + year)['year'] = Year
            
            # Appending the dataframe 
            qualification = qualification.append(eval(track + '_' + year),ignore_index = True, sort=True)
        except:
            pass
        
# =============================================================================
# 2.2 Saving the data, since running is costly  
# =============================================================================
with open('/Users/PM/Documents/Projects/2. F1/1. Data/qualification.pickle', 'wb') as f:
    pickle.dump(qualification,f)

        
#%% 3. Data Cleaning

# =============================================================================
# 3.1 Opening appended file
# =============================================================================
with open('/Users/PM/Documents/Projects/2. F1/1. Data/qualification.pickle', 'rb') as f:
    qualification = pickle.load(f)     
       
# =============================================================================
# 3.2 General cleaning 
# =============================================================================

# Delete trailing spaces in column names
qualification.rename(columns=lambda x: x.strip(), inplace = True)

# Delete empty rows - First change them to NaN and then drop them
qualification.replace(to_replace = "", value = np.nan, inplace = True)
qualification.dropna(subset = ['Driver','Engine'], inplace = True)

# If no round was driven because of an accident, time is marked as "-" and should be dropped
qualification = qualification[~qualification['Time'].str.contains("-")]

# Qualification time still relevant, even if driver did not start the actual race
# If the above situation occurs, then a driver's name has a trailing star symbol
qualification['Driver'] = qualification['Driver'].str.rstrip(' *')

# We are only interested in the last name of the driver
qualification['Driver'] = qualification['Driver'].str.split().str[-1]

# If somebody has the pole position, then the gap should be set to zero
qualification['Gap'][qualification['Pos'] == str(1)] = 0  

# The Gap between times should be a float variable
qualification['Gap'] = qualification['Gap'].astype(float)

# Capitalize the strings
qualification = qualification.applymap(lambda s:s.capitalize() if type(s) == str else s)

# =============================================================================
# 3.2 Saving the data
# =============================================================================

with open('/Users/PM/Documents/Projects/2. F1/1. Data/qualification_clean.pickle', 'wb') as f:
    pickle.dump(qualification,f)


