# Authors: Fabian Levén, Fredrik Nyström
# 
# This file will not work without a username
# and password to Nordpools API.
 
import pandas as pd
import numpy as np
from ftplib import FTP
import os
import xlrd
import csv
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt

class PricesData():
    def __init__(self, year, month = None, day = None):
        self.year = year
        self.year_ext = str(year)[-2:]
        self.filename_xls = f'sundsek{self.year_ext}.xls'
        self.filename_csv = f'sundsek{self.year_ext}.csv'
        self.month = month
        self.day = day
        self.path_to_sundsvall = '/Elspot/Elspot_prices/Sweden/SE2_Sundsvall'
        self.path_to_dir = self.path_to_sundsvall if year == datetime.today().year else f'{self.path_to_sundsvall}/{self.year}'


def main():
    data = PricesData(2022)
    #get_ftp_data(data)
    #xls_to_csv('../Data/', data.filename_xls)

    W0422 = ['2022-01-24', '2022-01-30']

    daily_price = get_daily_price(W0422[0], W0422[1], f'../Data/{data.filename_csv}')
    
    daily_consumption = get_daily_consumption_for_days_in_file('../Data/consumption_W0422.csv')

    daily_cost = cost_per_day(daily_price, daily_consumption)

    plot(daily_cost, W0422)

def plot(daily_cost, date_interval):
    ##### PLOTTING #####
    start_date = date_interval[0]
    end_date = date_interval[1]

    np_start_date = datetime.strptime(start_date, '%Y-%m-%d')
    np_end_date = datetime.strptime(end_date, '%Y-%m-%d')


    # increments date på one day
    end_date_arange = datetime.strftime(datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1),'%Y-%m-%d')
    x = np.arange(np_start_date, end_date_arange, np.timedelta64(1, 'h') )
    y = flatten(daily_cost)
    
    figure, axis = plt.subplots()
    figure.suptitle(f'Daily costs during interval {start_date} - {end_date}')

    axis.plot(x, y, linewidth = 0.5, color = 'red')

    axis.set_xlabel('Time [days]')
    axis.set_xlim(np_start_date, np_end_date)

    axis.set_ylabel('Cost [sek]')
    axis.set_ylim(0, max(y))

    plt.tight_layout()
    plt.show()

# takes a 2D matrix and turns inte into an array 
def flatten(l):
    return [item for sublist in l for item in sublist]


def cost_per_day(price, consumption):
    if len(price) != len(consumption):
        raise Exception('Not the same length of the lists')
    return np.array(price)*np.array(consumption)
    

def xls_to_csv(path_to_file, filename):
    sheet = xlrd.open_workbook(path_to_file + filename).sheet_by_index(0)
    csv_file_name = os.path.splitext(filename)[0] + '.csv'
    col = csv.writer(open(path_to_file + csv_file_name, 'w', newline="", encoding='utf8'))

    # writing the data row by row into csv file
    for row in range(sheet.nrows):
        col.writerow(sheet.row_values(row))

    # How to convert to DataFrame 
    # df = pd.DataFrame(pd.read_csv(path_to_file + csv_file_name, encoding='utf-8'))

def get_daily_consumption_for_days_in_file(file_path):
    file_data = pd.read_csv(file_path)
    result = []

    for day in range(0, len(file_data), 24):
        daily_consumption = []
        for hour in range(day, day+24):
            daily_consumption.append(float(file_data.iloc[hour]['kWh']) / 1000) # convert kWh to MWh
        result.append(daily_consumption)

    return result

 # Start and end date at format: yyyy-mm-dd including the end date, the cost is in kr/MWh
def get_daily_price(start_date, end_date, file_path):
    start_date = date.fromisoformat(start_date)
    end_date = date.fromisoformat(end_date)
    diff_date_days = (end_date - start_date).days + 1 

    file_data = pd.read_csv(file_path)
    result = []

    start_row = 4 + int(start_date.strftime('%j'))
    end_row = start_row + diff_date_days

    col = 1
    for day in range(start_row, end_row, 1):
        daily_cost = []
        for hour in range(col, col + 25, 1): # 3B gives us 25 hours
            if hour == 4:
                continue
            else:
                daily_cost.append(float(file_data.iloc[day][hour]))
        result.append(daily_cost)

    return result


def get_ftp_data(data: PricesData):
    ftp = connect_to_ftp()
    ftp.cwd(data.path_to_dir)
    try:
        with open('../Data/' + data.filename_xls, 'wb') as localfile:
            ftp.retrbinary('RETR ' + data.filename_xls, localfile.write, 1024)
    except:
        print(f'No such file in API')
    finally:
        ftp.quit()

# connect to ftp server and get API, dont forget to call ftp.quit() afterwards
def connect_to_ftp():
    ftp_url = 'ftp.nordpoolgroup.com'
    user = 'studentnordic'
    password = 'noRdic_2022'
    ftp = FTP(ftp_url)
    ftp.login(user=user, passwd=password)
    return ftp


def get_consumption():
    weeks = ['W0422', 'W1122', 'W2722']
    consumption = []
    for week in weeks:
        consumption.append(get_daily_consumption_for_days_in_file(f'Data/consumption_{week}.csv'))
    return consumption

def get_elecricity_prices():
    W0422 = ['2022-01-24', '2022-01-30']
    W1122 = ['2022-03-14', '2022-03-20']
    W2722 = ['2022-07-04', '2022-07-10']
    data = PricesData(2022)
    #utils.get_ftp_data(data)
    #utils.xls_to_csv('Data/', data.filename_xls)
    daily_price_W0422 = get_daily_price(W0422[0], W0422[1], f'Data/{data.filename_csv}')
    daily_price_W1122 = get_daily_price(W1122[0], W1122[1], f'Data/{data.filename_csv}')
    daily_price_W2722 = get_daily_price(W2722[0], W2722[1], f'Data/{data.filename_csv}')
    daily_price_three_weeks = [daily_price_W0422, daily_price_W1122, daily_price_W2722]
    return daily_price_three_weeks

if __name__ == '__main__':
    main()