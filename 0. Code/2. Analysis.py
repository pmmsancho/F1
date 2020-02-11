#%% 0. Starting

# =============================================================================
# 0.1 Loading in the pickle data
# =============================================================================

with open('/Users/PM/Documents/Projects/2. F1/1. Data/qualification_clean.pickle', 'rb') as f:
    qual_clean = pickle.load(f)


#%% 1. Restrictions
    
# =============================================================================
# 1.1 Selecting only relevant variables
# =============================================================================

# Needed variables
relevant_var = ['Chassis', 'Driver', 'Engine', 'Gap', 'Pos', 'Country', 'Year']
quali = qual_clean[relevant_var]

# =============================================================================
# 1.2 Qualification rounds
# =============================================================================

# Changing data format
quali['Pos'] = quali['Pos'].astype(int)

# Generating the new column called Round
quali['Round'] = 1
quali['Round'][quali['Pos'].between(11,15)] = 2
quali['Round'][quali['Pos'].between(1,10)] = 3

# =============================================================================
# 1.3 Restricting data - Since different Q-Rounds are not comparable
# =============================================================================

# Only keeping drivers who drove in Q3
q3 = quali[quali['Round'] == 3]

# =============================================================================
# 1.4 Outliers
# =============================================================================

# Assuming that if a driver has a bigger gap than the 95-percentile, he did not try
q3 = q3[q3['Gap'].quantile(.95) > q3['Gap']]

#%% 2. ANOVA and Boxplot

# =============================================================================
# 2.1 Required Packages & Cutoff
# =============================================================================

# Packages
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multicomp import MultiComparison
from statsmodels.tsa.stattools import adfuller
import openpyxl


# Cutoff for statistical purposes
cutoff = 30

# Path
path = '/Users/PM/Documents/Projects/2. F1/2. Output'

# =============================================================================
# 2.2 Function for Boxplots and Test Statistics
# =============================================================================

def boxplot(data, x_var):
    plt.figure()
    box = sns.boxplot(x = x_var, 
                     y = 'Gap', 
                     data = data,
                     color = 'gold'
                     )
    box.set_xlabel(x_var, fontsize = 15)
    box.set_ylabel('Gap to pole position (in sec.)', fontsize = 15)
    plt.xticks(rotation=90)
    
    # Saving file
    fig= box.get_figure()
    fig.savefig(path + '/0. Graphs/' + x_var + '.png',bbox_inches='tight')
    plt.close()

def append(path,data,name):
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
         writer.book = openpyxl.load_workbook(path)
         data.to_excel(writer, name)

def anova(data, variable):    
    results = ols('Gap ~ '+ variable, data = data).fit()
    table = sm.stats.anova_lm(results, typ = 2, robust = 'hc3')
    path_total = path + '/1. Excel/ANOVA.xlsx'
    append(path_total,table,variable)
    
def direct_comparison(data, variable, extension, name):        
    mc = MultiComparison(data['Gap'], data[variable])
    Results = mc.tukeyhsd()
    df = pd.DataFrame(data=Results._results_table.data[1:], columns=Results._results_table.data[0])
    path_total = path + extension
    df = df.astype(str)
    append(path_total,df,name)
    
def dickey_fuller(Driver):
    X = q3_top10[q3_top10['Driver'] == Driver]['Gap'].values
    result = adfuller(X)
    results = [result[0], result[1],None,result[4]['1%'],result[4]['5%'],result[4]['10%']]
    df = pd.DataFrame(data = {'Statistics': string,'Value': results})
    path_total = path + '/1. Excel/ADF.xlsx'
    append(path_total,df,driver)    

# =============================================================================
# 2.3 Boxplot and ANOVA
# =============================================================================

# Create empty excel sheets
wb = openpyxl.Workbook()
wb.save(path + '/1. Excel/ANOVA.xlsx')    
wb.save(path + '/1. Excel/Direct.xlsx')    
wb.save(path + '/1. Excel/ADF.xlsx')    

# Looping variables
variables = ['Chassis', 'Country', 'Driver','Year','Engine']

for variable in variables: 

    # Cutoff
    q3_subset = q3.groupby(variable).filter(lambda x : len(x) >= cutoff)
    
    # Boxplots between Tracks
    boxplot(q3_subset,variable)
    
    # ANOVA
    anova(q3_subset, variable)
    
    # Direct comparison
    direct_comparison(q3_subset, variable, '/1. Excel/Direct.xlsx',variable)

# =============================================================================
# 2.4 Stationarity of Time Gap 
# =============================================================================

# Doing the test on the most appearing ten drivers
top10 = q3['Driver'].value_counts().index[0:10]
q3_top10 = q3[q3['Driver'].isin(top10)]

# Time function
q3_top10['Time'] = q3_top10['Country'] + ' ' + q3_top10['Year']

# Reshaping the data
graph_top10 = q3_top10.pivot(index='Time', columns='Driver', values='Gap')
fig, ax = plt.subplots(figsize=(20,10))
graph_top10.plot(ax = ax)
plt.xticks(rotation=45, fontsize = 12)
plt.xlabel('Races over Time', fontsize=18)
plt.ylabel('Gap to pole position (in sec.)', fontsize=18)
leg = ax.legend(prop = {'size' : 12})
fig.savefig('/Users/PM/Documents/Projects/2. F1/2. Output/0. Graphs/Stationarity.png',
            bbox_inches='tight')


# Dickey Fuller Testing
string = ['ADF Statistic: %f',
          'p-value: %f',
          'Critical Values:',
          '1%',
          '5%',
          '10%'
          ]

for driver in top10:
    dickey_fuller(driver)

#%% 3. Regressions focusing only on driver and chassie
    
# =============================================================================
# 3.1 Restricting
# =============================================================================

# Keeping only necessary variables
relevant_var = ['Gap', 'Driver', 'Chassis','Year','Country','Engine']
q3_reg = q3[relevant_var]

# We want to have at least 30 observations of all chasssies as well as all drivers
q3_reg = q3_reg.groupby('Driver').filter(lambda x : len(x) >= cutoff)
q3_reg = q3_reg.groupby('Chassis').filter(lambda x : len(x) >= cutoff)

# Creating an interaction term for the dummies
q3_reg_interaction = q3_reg.copy()
q3_reg_interaction['Interaction'] = q3_reg['Driver'] + q3_reg['Chassis']

# Creating dummy variables with all categorical data available
q3_dummies = pd.get_dummies(q3_reg_interaction)

# =============================================================================
# 3.2 Regression over entire data
# =============================================================================

# Empty excel container
wb.save(path + '/1. Excel/Regression.xlsx')    
wb.save(path + '/1. Excel/Correlation.xlsx')    

# Regression analysis
result = sm.OLS(endog = q3_dummies.iloc[:,0], exog = q3_dummies.iloc[:,1:]).fit(cov_type='HC3')
regression = pd.concat((result.params, result.tvalues), axis=1)
regression.to_excel(path + '/1. Excel/Regression.xlsx')

# QQ Plot
res = result.resid
fig = sm.qqplot(res)
plt.show()

# =============================================================================
# 3.3 Correlation Matrix
# =============================================================================

# Correlation matrix in order to show the multicollinearity problem
correlation = q3_dummies.iloc[:,1:].corr()
correlation.to_excel(path + '/1. Excel/Correlation.xlsx')

#%% 4. Definite results - Within Car

# Empty excel container
wb.save(path + '/1. Excel/Definite.xlsx')    

# =============================================================================
# Verstappen vs. Ricciardo
# =============================================================================
verric = q3_reg[q3_reg['Driver'].isin(['Verstappen','Ricciardo']) & q3_reg['Chassis'].isin(['Red Bull'])]
direct_comparison(verric, 'Driver', '/1. Excel/Definite.xlsx','verric')

# =============================================================================
# Vettel vs. Raikkonen
# =============================================================================
vetrai = q3_reg[q3_reg['Driver'].isin(['Vettel','Raikkonen']) & q3_reg['Chassis'].isin(['Ferrari'])]
direct_comparison(vetrai, 'Driver', '/1. Excel/Definite.xlsx','vetrai')

# =============================================================================
# Hamilton vs. Bottas
# =============================================================================
hambot = q3_reg[q3_reg['Driver'].isin(['Hamilton','Bottas']) & q3_reg['Chassis'].isin(['Mercedes'])]
direct_comparison(hambot, 'Driver', '/1. Excel/Definite.xlsx','hambot')

#%% 5. Car effect

# Empty excel containers
wb.save(path + '/1. Excel/Car Effect.xlsx')    

# =============================================================================
# 5.1 Getting the coefficients of all drivers 
# =============================================================================

drivers = q3_reg['Driver'].unique()

# Looping over all drivers
for driver in drivers:
    
    # Restricting data to each driver
    relevant_data = q3_reg[q3_reg['Driver'] == driver]
    
    # 
    relevant_dummies = pd.get_dummies(relevant_data)
    dependent = relevant_dummies['Gap']
    independent = relevant_dummies.iloc[:,2:]
    result = sm.OLS(endog = dependent, exog = independent).fit(cov_type='HC3')
    coefficients = result.params
    append(path + '/1. Excel/Car Effect.xlsx', coefficients, driver)
    
    # Counting how many races are done for each driver
    relevant_data = q3_reg[q3_reg['Driver'] == driver]
    relevant_data['Gap'].mean()
    relevant_data['Chassis'].value_counts()
