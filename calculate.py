from DataHandling.SVK_data import SVK_data as SVK
import DataHandling.utils as utils
from Algorithm.fcr import BESS
from Algorithm.peak_shaving import run_all_weeks

SVK_DATA = SVK()

class AllData: 
    def __init__(self, electricity_prices, consumption, cost_hourly, total_cost):
        self.electricity_prices = electricity_prices
        self.consumption = consumption
        self.cost_hourly = cost_hourly
        self.total_cost = total_cost


def calculate(capacity, buffer_size, min_charge, max_charge, dod, power):
    bess = BESS(capacity, buffer_size, min_charge, max_charge, dod, power, SVK_DATA)
    fcr_profit_day = bess.fcr_start_to_date()
    print(fcr_profit_day)
    return fcr_profit_day

def calculate_peak (capacity, buffer_size, min_charge, max_charge, dod, power):
    bess = BESS(capacity, buffer_size, min_charge, max_charge, dod, power, SVK_DATA)
    peak_savings = run_all_weeks(bess)
    return peak_savings

def total_profit(list_of_tuples):
    profit = 0
    for elem in list_of_tuples:
        profit += elem[1]
    return profit

# Lista med tuples med vilken algoritm vi använde och profit per dag under ett år. 
def get_best_algorithm_values(fcr_profit, peak_shavings_profit):
    ret_value = []
    for i in range(364):
        if fcr_profit > peak_shavings_profit[i]: 
            ret_value[i] = ('fcr', fcr_profit)
        else:
            ret_value[i] = ('peak_shaving', peak_shavings_profit[i])
    return ret_value

def get_total_cost(weeks):
    total_cost = 0
    for week in weeks:
        for day in week:
            for hour in day:
                total_cost = total_cost + hour

    total_cost = total_cost * (52/3)
    return total_cost

def get_consumption():
    weeks = ['W0422', 'W1122', 'W2722']
    consumption = []
    for week in weeks:
        consumption.append(utils.get_daily_consumption_for_days_in_file(f'Data/consumption_{week}.csv'))
    return consumption

def get_elecricity_prices():
    W0422 = ['2022-01-24', '2022-01-30']
    W1122 = ['2022-03-14', '2022-03-20']
    W2722 = ['2022-07-04', '2022-07-10']
    data = utils.PricesData(2022)
    #utils.get_ftp_data(data)
    #utils.xls_to_csv('Data/', data.filename_xls)
    daily_price_W0422 = utils.get_daily_price(W0422[0], W0422[1], f'Data/{data.filename_csv}')
    daily_price_W1122 = utils.get_daily_price(W1122[0], W1122[1], f'Data/{data.filename_csv}')
    daily_price_W2722 = utils.get_daily_price(W2722[0], W2722[1], f'Data/{data.filename_csv}')
    daily_price_three_weeks = [daily_price_W0422, daily_price_W1122, daily_price_W2722]
    return daily_price_three_weeks

