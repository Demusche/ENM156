# Author: Salam Hani
# 
# mimer.svk API
#
# Reads data from mimer.svk.se
# Makes it possible to retrieve data from a certain time
# in the past, or in the future of the current day.
# 
# Available data is solar-, wind-, water- fusion- and heat-production
#
# SE = Solenergiproduktion
# VI = Vindkraftproduktion
# VA = Vattenkraftproduktion
# KK = Kärnkraftproduktion
# OK = Övrig värmekraftproduktion
#
# • Frequency prices are available for the entire current day.
# • Production prices are only available from yesterday and past that.
# • Consumption data is also available although only from /atleast/ 
#   one month in the past. Use nearest_data to see the newest data
#   available.
#   
# ________________________________________________________________
# IMPORTANT parameters:
#
# area: 
# 0 = entire Sweden, 
# 1 = elområde 1 
# 2 = elområde 2 
# 3 = elområde 3
# 4 = elområde 4
#
# year: is always entered as four digits
# ________________________________________________________________
#
# All data is returned in float type
#
import pandas as pd
import datetime as dt
import calendar as cd
import sys, os
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class SVK_data():
    ######### INITIATION ###########
         
    # Constructor which selects current date as selected date - Default values
    def __init__(self):
        self.area = 0
        self.curr_day = dt.datetime.now().strftime("%d")
        self.curr_month = dt.datetime.now().strftime("%m")
        self.curr_year = dt.datetime.now().strftime("%Y")
        self.curr_date = dt.date(int(self.curr_year), int(self.curr_month), int(self.curr_day))
        self.curr_datetime = dt.datetime(int(self.curr_year), int(self.curr_month), int(self.curr_day))
        self.download_csv_file_from_beginning_of_time()
        self.df = pd.read_csv('downloaded.csv', delimiter=';')
    
    ######### SELECTION ###########

    # Downloads the file with all data available upon creating an instance of SVK_data
    def download_csv_file_from_beginning_of_time(self):
        req = requests.get("https://mimer.svk.se/PrimaryRegulation/DownloadText?periodFrom=" + str(1) + "%2F" + str(1) + "%2F" + str(2022) + "%2000%3A00%3A00&periodTo=" + str(self.curr_month)+ "%2F" + str(self.curr_day) + "%2F" + str(self.curr_year) + "%2000%3A00%3A00&auctionTypeId=1&productTypeId=0")
        csv_file = open('downloaded.csv', 'wb')
        csv_file.write(req.content)
        csv_file.close()
    
    def select_area(self, area: int):
        if area > -1 and area < 5:
            self.area = area
            self.update_links()
        else:
            raise Exception("Error: area can only be between 0-4")
        
    ######### FREQUENCY PRICES ###########
    
    # Returns FCRD-UP price of the selected hour from the current day
    # This function can get hourly price directly from mimer.svk
    def FCRDUPP_now_price_hourly(self, hour: int):
        curr_day = dt.datetime.now().strftime("%d")
        curr_month = dt.datetime.now().strftime("%m")
        curr_year = dt.datetime.now().strftime("%Y")
        if (hour > dt.datetime.now().strftime("%-H")):
            raise Exception("Error: function - FCRDUPP_now_price_hourly\n \
                            Selected hour can not be in the future.")
        df = pd.read_csv('https://mimer.svk.se/PrimaryRegulation/DownloadText?periodFrom=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) +
                         '%2000%3A00%3A00&periodTo=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) + '%2000%3A00%3A00&auctionTypeId=1&productTypeId=0', delimiter=';')
        price = float(df.iloc[hour, 8].replace(',', '.'))
        return price
    
    # Returns FCRD-DOWN price of the selected hour from the current day
    # This function can get hourly price directly from mimer.svk
    def FCRDNER_now_price_hourly(self, hour: int):
        curr_day = dt.datetime.now().strftime("%d")
        curr_month = dt.datetime.now().strftime("%m")
        curr_year = dt.datetime.now().strftime("%Y")
        if (hour > dt.datetime.now().strftime("%-H")):
            raise Exception("Error: function - FCRDUPP_now_price_hourly\n \
                            Selected hour can not be in the future.")
        df = pd.read_csv('https://mimer.svk.se/PrimaryRegulation/DownloadText?periodFrom=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) +
                         '%2000%3A00%3A00&periodTo=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) + '%2000%3A00%3A00&auctionTypeId=1&productTypeId=0', delimiter=';')
        price = float(df.iloc[hour, 15].replace(',', '.'))
        return price
    
    # Returns FCRD Up price of selected date and time
    # This function gets data from the downloaded file, thus making it
    # quick to work with to write graphs etc.
    def FCRDUPP_price_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        beginning_of_year = dt.date(int(self.curr_year), 1, 1)
        total_hours_of_year = int(
            (issuedate - beginning_of_year).total_seconds() // 3600) + hour
        if diff_date.total_seconds() > -86400:
            if year <= 2021:
                raise Exception("Error: function - FCRDUPP_price_date_total\n \
                            The selected date can not be before year 2022")
            else:
                price = float(
                    self.df.iloc[total_hours_of_year, 8].replace(',', '.'))
            return price
        else:
            raise Exception("Error: function - FCRDNER_price_date()\n \
                            The selected date can not be in the future.")

    # Returns FCRD Down price of selected date and time
    # This function gets data from the downloaded file, thus making it
    # quick to work with to write graphs etc.
    def FCRDNER_price_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        beginning_of_year = dt.date(int(self.curr_year), 1, 1)
        total_hours_of_year = int((issuedate - beginning_of_year).total_seconds() // 3600) + hour
        if diff_date.total_seconds() > -86400:
            if year <= 2021:
                raise Exception("Error: function - FCRDUPP_price_date_total\n \
                            The selected date can not be before year 2022")
            else:
                price = float(self.df.iloc[total_hours_of_year, 15].replace(',', '.')) 
            return price
        else:
            raise Exception("Error: function - FCRDNER_price_date()\n \
                            The selected date can not be in the future.")
    

    # Returns sum of all FCRD-UP prices of the current day each hour (sum of 24 terms)
    def FCRDUPP_now_price_total(self):
        curr_day = dt.datetime.now().strftime("%d")
        curr_month = dt.datetime.now().strftime("%m")
        curr_year = dt.datetime.now().strftime("%Y")
        df = pd.read_csv('https://mimer.svk.se/PrimaryRegulation/DownloadText?periodFrom=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) +
                         '%2000%3A00%3A00&periodTo=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) + '%2000%3A00%3A00&auctionTypeId=1&productTypeId=0', delimiter=';')
        price = float(df.iloc[24, 8].replace(',', '.'))
        return price
    
    # Returns sum of all FCRD-DOWN prices of the current day each hour (sum of 24 terms)
    def FCRDNER_now_price_total(self):
        curr_day = dt.datetime.now().strftime("%d")
        curr_month = dt.datetime.now().strftime("%m")
        curr_year = dt.datetime.now().strftime("%Y")
        df = pd.read_csv('https://mimer.svk.se/PrimaryRegulation/DownloadText?periodFrom=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) +
                         '%2000%3A00%3A00&periodTo=' + str(curr_month) + '%2F' + str(curr_day) + '%2F' + str(curr_year) + '%2000%3A00%3A00&auctionTypeId=1&productTypeId=0', delimiter=';')
        price = float(df.iloc[24, 15].replace(',', '.'))
        return price
    
    ######### SOLAR PRODUCTION ###########
    
    def SE_produced_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=SE', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - SE_produced_date()\n \
                            The selected date can not be in the future nor the current day.")
    
    def SE_produced_date_area(self, year: int, month: int, day: int, hour: int, area: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=SE', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - SE_produced_date_area()\n \
                            The selected date can not be in the future nor the current day.")
    
    ######### WIND PRODUCTION ###########
    
    def VI_produced_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=VI', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - VI_produced_date()\n \
                            The selected date can not be in the future nor the current day.")
    
    def VI_produced_date_area(self, year: int, month: int, day: int, hour: int, area: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=VI', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - VI_produced_date_area()\n \
                            The selected date can not be in the future nor the current day.")


    ######### WATER PRODUCTION ###########
    
    def VA_produced_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=VA', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - VA_produced_date()\n \
                            The selected date can not be in the future nor the current day.")
    
    def VA_produced_date_area(self, year: int, month: int, day: int, hour: int, area: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=VA', delimiter=';')
            production = float(df.iloc[hour, 1].replace(',', '.'))
            return production
        else:
            raise Exception("Error: function - VA_produced_date_area()\n \
                            The selected date can not be in the future nor the current day.")
    
    ######### FUSION PRODUCTION ###########

    
    def KK_produced_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=KK', delimiter=';')
            production = float(df.iloc[hour, 1])
            return production
        else:
            raise Exception("Error: function - KK_produced_date()\n \
                            The selected date can not be in the future nor the current day.")
    
    def KK_produced_date_area(self, year: int, month: int, day: int, hour: int, area: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=KK', delimiter=';')
            production = float(df.iloc[hour, 1])
            return production
        else:
            raise Exception("Error: function - KK_produced_date_area()\n \
                            The selected date can not be in the future nor the current day.")
    
    ######### HEAT PRODUCTION ###########

    def OK_produced_date(self, year: int, month: int, day: int, hour: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=OK', delimiter=';')
            production = float(df.iloc[hour, 1])
            return production
        else:
            raise Exception("Error: function - OK_produced_date()\n \
                            The selected date can not be in the future nor the current day.")
    
    def OK_produced_date_area(self, year: int, month: int, day: int, hour: int, area: int):
        issuedate = dt.date(year, month, day)
        diff_date = self.curr_date - issuedate
        if diff_date.total_seconds() > 0:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=OK', delimiter=';')
            production = float(df.iloc[hour, 1])
            return production
        else:
            raise Exception("Error: function - OK_produced_date_area()\n \
                            The selected date can not be in the future nor the current day.")
    
    ######### Consumption of Electricity ###########
    
    def conumption_date_hourly_area(self, year: int, month: int, day: int, hour: int, area: int):
        df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=TL&IsConsumption=True', delimiter=';')
        try:
            consumption = float(df.iloc[hour, 1].replace(",", "."))
            return consumption
        except:
            raise Exception(self.nearest_data())
            

    def conumption_date_hourly(self, year: int, month: int, day: int, hour: int):
        df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(0) + '&ProductionSortId=TL&IsConsumption=True', delimiter=';')
        try:
            consumption = float(df.iloc[hour, 1].replace(",", "."))
            return consumption
        except:
            raise Exception(self.nearest_data())

    def consumption_date_area_total(self, year: int, month: int, day: int, area: int):
        df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(area) + '&ProductionSortId=TL&IsConsumption=True', delimiter=';')
        try:
            consumption = float(df.iloc[24, 1].replace(",", "."))
            return consumption
        except:
            raise Exception(self.nearest_data())

    def consumption_date_total(self, year: int, month: int, day: int):
        df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(0) + '&ProductionSortId=TL&IsConsumption=True', delimiter=';')
        try:
            consumption = float(df.iloc[24, 1].replace(",", "."))
            return consumption
        except:
            raise Exception(self.nearest_data())


    def nearest_data(self):
        day = int(self.curr_day)
        month = int(self.curr_month) 
        year = int(self.curr_year) 
        
        while True:
            df = pd.read_csv('https://mimer.svk.se/ProductionConsumption/DownloadText?PeriodFrom=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&PeriodTo=' + str(month) + '%2F' + str(day) + '%2F' + str(year) + '%2000%3A00%3A00&ConstraintAreaId=SN' + str(self.area) + '&ProductionSortId=TL&IsConsumption=True', delimiter=';')
            try:
                consumption = float(df.iloc[24, 1].replace(",", "."))
            except:
                consumption = 1
                pass
            
            if consumption != None and consumption < 0.0:
                return "Nearest available data for electricity consumption is " + str(year) + "-" + str(month) + "-" + str(day)
            if day == 1:
                if month == 1:
                    year -= 1
                    day = 31
                    month = 12
                else:
                    month -= 1
                    day = cd.monthrange(year, month)[1]
            else: 
                    day -= 1
