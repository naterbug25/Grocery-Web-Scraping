from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import pandas as pd
import plotly.graph_objects as px
import undetected_chromedriver.v2 as uc 

Web_Driver = uc.Chrome() 

MAX_WEB_DELAY = 30 # (Sec) Time we wait on page to load

#*** Aldi ***
ALDI_MAIN_WEB_PAGE = "https://www.instacart.com/store/aldi/storefront"
ALDI_PRICE_CLASS = ["css-1u4ofbf"]

#*** Kroger ***
INSTA_CART_MAIN_WEB_PAGE = "https://www.instacart.com/store/kroger/storefront"
KROGER_PRICE_CLASS = ["css-1u4ofbf"]

#*** Walmart ***
WALMART_MAIN_WEB_PAGE = "https://www.instacart.com/store/walmart/storefront"
WALMART_PRICE_CLASS = ["css-1u4ofbf"]

def Read_Store_Info(_Store_Name): # Get the store info
    _All_Store_Data = pd.read_csv("Database.csv") # Read in the csv to a dataframe
    # Remove all data not applicable to our store
    for Col_Name in _All_Store_Data.columns:
        if (Col_Name[0:len(_Store_Name)] != _Store_Name) and (Col_Name != "Category"): # Look for the store name and if its not the Category column
            _All_Store_Data = _All_Store_Data.drop(columns = Col_Name) # Drop the stores not used
    _All_Store_Data.insert(3,"Price",[None] * len(_All_Store_Data),True) # Add Price Column
    return _All_Store_Data

def Find_Item_Price(_Item,_Link,_Class_List): # TODO _Item is for using search bar if not found
    Web_Driver.get(_Link) # Update the webpage
    Price="0" # Zero price 
    for _Class in _Class_List: # Increment through the list of possible class names
        _Cntr = 0 # Count how many retry
        while (True):
            try:
                elem = WebDriverWait(Web_Driver, MAX_WEB_DELAY).until(EC.presence_of_element_located((By.CLASS_NAME,_Class))) # Wait for a banner to appear
                break 
            except: 
                _Cntr +=1
                print("\nPrice Check - Update CLASS_NAME, element not found")
                print("Item: ",_Item)
                print("Link: ",_Link,"\n")
                if (_Cntr >=3):
                    return 0
                else:
                    Web_Driver.get(_Link) # Update the webpage
        Price = (Web_Driver.find_element(By.CLASS_NAME,_Class).text).replace("$","") # Get the price div
        if "reg" in Price: # Instacart
            Price = Price[Price.find("reg. ")+len("reg. "):] # Remove sale price
        if "/" in Price:
            Price = Price[:Price.find(" /")] # Remove weight
        if float(Price) > 0:
            break # We made it
    return float(Price)
    
def Store_Data_Extraction(_Store,_Link,_Class):
    # Open main webpage
    Web_Driver.get(_Link) # Get the webpage
    Store_Data = Read_Store_Info(_Store) # Read in info from local db

    try:
        elem = WebDriverWait(Web_Driver, MAX_WEB_DELAY).until(EC.presence_of_element_located((By.CLASS_NAME,"css-wz9ryu"))) # Wait for a banner to appear on main page
    except: 
        print("Update CSS_SELECTOR, element not found")

    # Loop through looking for all of the items            
    for Idx, Item in Store_Data.iterrows():
        Store_Data["Price"].iloc[Idx] = Find_Item_Price(Item[1],Item[2],_Class) # Open the link and extract price
    return Store_Data

Results = pd.DataFrame() # Blank DF

# *** Aldi ***
Temp_Data = Store_Data_Extraction("Aldi",ALDI_MAIN_WEB_PAGE,ALDI_PRICE_CLASS) # Get the prices of items in database
Results["Category"] = Temp_Data["Category"] # Get the first column of categorys only needed once
Results["Aldi-Price"] = Temp_Data["Price"]

# #*** Kroger ***
Temp_Data = Store_Data_Extraction("Kroger",INSTA_CART_MAIN_WEB_PAGE,KROGER_PRICE_CLASS) # Get the prices of items in database
Results["Kroger-Price"] = Temp_Data["Price"]

# # *** Walmart ***
Temp_Data = Store_Data_Extraction("Walmart",WALMART_MAIN_WEB_PAGE,WALMART_PRICE_CLASS) # Get the prices of items in database
Results["Walmart-Price"] = Temp_Data["Price"] # Get the first column of categorys only needed once

# *** Store results ***
Current_DT = datetime.now().strftime("%Y%m%d%H%M")  # Filename
Filename = "Results"+"_"+Current_DT
Results.to_csv(Filename+".csv")  # Store data

# *** Plot stuff ***
Plot_Layout = px.Layout(
    title=Filename,
    xaxis=dict(
        title="Item"
    ),
    yaxis=dict(
        title="Price ($)"
    ) ) 

Plot = px.Figure(
    layout = Plot_Layout,
    data=[px.Bar(
    name = 'Aldi',
    x = Results["Category"],
    y = Results["Aldi-Price"],
    marker = dict(color="Gold")),
    px.Bar(
    name = 'Kroger',
    x = Results["Category"],
    y = Results["Kroger-Price"],
    marker = dict(color="Red")
   ),
    px.Bar(
    name = 'Walmart',
    x = Results["Category"],
    y = Results["Walmart-Price"],
    marker = dict(color="Blue")
   )
])
Plot.update_traces(marker_line_color = 'black', marker_line_width = 2)
Plot.write_html(Filename+".html")
Plot.show()
