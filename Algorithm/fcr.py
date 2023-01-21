import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from DataHandling.SVK_data import SVK_data as SVK
import datetime as dt
import calendar as cd


class BESS:

    def __init__(self, capacity, buffer_size, min_charge, max_charge, dod, power, SVK_DATA):
        self.capacity = capacity        # Total capacity [MWh]
        self.buffer_size = buffer_size  # Buffer size [% of capacity]
        self.dod = dod                  # Depth of discharge. IRRELEVANT
        self.power = power              # Maximum power for charging/discharging [MW]
        self.charge = 0                 # Current charge [MWh]
        self.buffer = 0                 # Buffer size [MWh]
        self.min_charge = min_charge    # Lower threshold for battery [% of capacity]
        self.max_charge = max_charge    # Higher threshold for battery [% of capacity]
        self.day = int(dt.datetime.now().strftime("%d"))    # Current date (day)    [int]
        self.year = int(dt.datetime.now().strftime("%Y"))   # Current date (month)  [int]
        self.month = int(dt.datetime.now().strftime("%m"))  # Current date (year)   [int]
        self.data = SVK_DATA    # FCR data

        # Availability is decided by how big the buffer size and depth of discharge is.
        self.availability = capacity - (capacity * (max(min_charge, buffer_size))) - capacity * (1-max_charge)
        self.available = 0
    
    def __str__(self):
        return f"Capacity: {self.capacity}MWh, Buffer size: {100 * self.buffer_size}%, Minimum charge: {100 * self.min_charge}%, Maximum charge: {100 * self.max_charge}%, Total charge: {round(self.charge, 3)} MWh, Buffer: {round(self.buffer, 3)}MWh, Available: {round(self.available, 3)}MWh"

    def init_with_buffer(self):
        self.buffer = self.capacity * self.buffer_size
        self.charge = self.capacity * self.buffer_size

    def enough_available_amount(self, amount_needed):
        return self.available <= amount_needed

    def charge_bess(self, amount):
        if(self.charge + amount <= self.capacity):
            self.charge += amount
            self.available = self.charge - self.buffer_size * self.capacity
            self.buffer = self.charge - self.available

    def discharge_bess(self, amount):
        if(self.available >= amount):
            self.charge -= amount
            self.available = self.charge - self.buffer_size * self.capacity
            self.buffer = self.charge - self.available

    
    def fcr_profit_per_day(self):
        start_date = dt.date(2022, 1, 1)
        end_date = dt.date(self.year, self.month, self.day)
        number_of_days = (end_date - start_date).days
        price_fcr_upp_down = self.data.FCRDNER_total_price_total_year() + self.data.FCRDUPP_total_price_total_year()

        return min(self.availability/2,self.power) * price_fcr_upp_down/(number_of_days*2)

    def fcr_profit_per_day_hourly(self, year, month, day):
        profit = 0
        for i in range(0,23,2):
            profit += self.availability/2 * (int(self.data.FCRDNER_price_date(year, month ,day, i)) + (int(self.data.FCRDUPP_price_date(year, month ,day, i))))
        return profit

    def fcr_start_to_date(self):
        start_year = 2022
        start_month = 1
        start_day = 1
        current_year = self.year
        current_month = self.month
        current_day = self.day
        profit = 0
        profit_array = [] 
        
       #current_hour = self.hour
        while(not(start_year == current_year and start_month == current_month and start_day == current_day)):
            profit = self.fcr_profit_per_day_hourly(start_year, start_month, start_day)
            profit_array.append(profit)
            #New month
            if(start_day == cd.monthrange(start_year, start_month)[1]):
                start_month += 1
                start_day = 1
            else:
                start_day += 1
            #New year
            if(start_month == 13):
                start_month = 1
                start_year += 1
        return profit_array

def main():

    bess = BESS(3, 0.3, 0.3, 0.9, 0, 1.5, SVK())
    print(bess.fcr_start_to_date())


    
if __name__ == "__main__":
    main()