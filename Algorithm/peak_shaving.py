# ====================================== IMPORTS ==================================================

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from DataHandling.SVK_data import SVK_data as SVK
import DataHandling.utils as data
import numpy as np
import matplotlib.pyplot as plt
from Algorithm.fcr import BESS

# from openmeteo_py import Hourly, Daily, Options, OWmanager   # Get Forecasting


# ====================================== ALGORITHM ================================================

# Extracts the active hours of a working day.
def get_active_hours_index(usage: list) -> tuple:
    # Average, adding 0.0005 to round up with 3 decimals.
    #avg = round((sum(usage) / len(usage)) + 0.0005, 3)
    avg = sum(usage) / len(usage)
    # Get start- and stop index of active period.
    above_avg = list(filter(lambda x: x > avg, usage))
    start_index = usage.index(above_avg[0])
    end_index = (len(usage) - 1) - list(reversed(usage)).index(above_avg[-1])
    return (start_index, end_index)


# Creates a list of the active hours.
def get_active_hours(usage: list) -> list:
    start_index, end_index = get_active_hours_index(usage)
    return usage[start_index: end_index + 1]


# Calculates the upper threshold.
#   Find the total consumption during active hours
#   Compare to BESS available amount when entering active period
#   Total consumption - available from BESS = what is needed from grid
#   Divide what is needed from grid by number of hours of active period
#   to get threshold for active period
def get_threshold(usage: list, bess: BESS) -> float:
    active_hours = get_active_hours(usage)
    if ((sum(active_hours) - bess.availability) / len(active_hours) < min(usage)):
        return sum(usage) / len(usage)
    return (sum(active_hours) - bess.availability) / len(active_hours)


# Extracts what hours to be charged on with a specified amount during inactive hours.
def get_charging_hours(costs: list, usage: list, threshold: float, bess: BESS) -> float:
    # Map index and usage to cost.
    index_cost_usage = list(zip(range(0, len(costs)), costs, usage))
    # Check on which part of the day that the inactive hours aren't.
    start_index, end_index = get_active_hours_index(usage)
    inactive_hours_w_index = index_cost_usage[0:start_index] + \
        index_cost_usage[end_index+1:]
    # Sort the mapped values after cost from lowest to highest.
    sorted_costs = sorted(inactive_hours_w_index, key=lambda t: t[1])
    # Calculate charge amount to handle the peak shaving of active hours.
    tot_charge_req = bess.availability - bess.available
    index_charge_amount = dict()
    new_charge = 0
    index = 0
    # Didnt have cheap hours :(
    if len(sorted_costs) <= 0:
        return index_charge_amount
    # Extract what hours that should be charged on to fully charge for as cheap as possible.
    while (new_charge < tot_charge_req):
        try:
            usage_cheapest = sorted_costs[index][2]
        except IndexError as e:
            print(e, "index:", index, "sorted_costs:", sorted_costs)
        # Find bottleneck of charge for the hour.
        # Charge min(bess.power, usage_during_cheapest - threshold, required charge)
        above_zero = filter(lambda x: x >= 0, [bess.power, threshold -
                           usage_cheapest, tot_charge_req - new_charge])
        added_charge = min(above_zero)
        new_charge += added_charge
        # Add hour to be charged at to the indices and the amount to be charged at that time.
        index_charge_amount[sorted_costs[index][0]] = added_charge
        index += 1
        # Could not charge fully. Return anyways
        if(index >= len(sorted_costs)):
            break
    return index_charge_amount


# Peak shaving throughout a day, with focus on charging on the cheapest hours.
def peak_shaving(costs: list, usage: list, bess: BESS) -> tuple:
    # Calculate threshold for active hours.
    threshold = get_threshold(usage, bess)
    # print("Threshold:", threshold)
    # Extract at what hours to charge and how much.
    index_charge_amount = get_charging_hours(costs, usage, threshold, bess)
    # Create array of size usage.
    usage_result = [0]*len(usage)
    cost_result = 0
    i = 0

    # Begin with charging on low hours (NON-CAUSAL RIGHT NOW)
    for index, charge in index_charge_amount.items():
        # print("To Charge:", charge)
        bess.charge_bess(charge)
        usage_result[index] = usage[index] + charge
        cost_result += costs[index] * usage_result[index]

    
    # Loop through the day and check whether to charge battery, use grid or use battery.
    while (i < len(usage)):
        # If the usage is over the threshold, discharge sufficient amount.
        if (usage[i] > threshold):
            # If there is enough charge to lower the usage to the threshold, use that amount.
            if (bess.available >= usage[i] - threshold):
                usage_result[i] = threshold
                cost_result += costs[i] * usage_result[i]
                bess.discharge_bess(usage[i] - threshold)
            # If battery isn't empty but there isn't enough charge to reach the threshold,
            # empty battery.
            elif (bess.available > 0):
                usage_result[i] = usage[i] - bess.available
                cost_result += costs[i] * usage_result[i]
                bess.discharge_bess(bess.available)
            # If battery is empty, just use the grid.
            else:
                usage_result[i] = usage[i]
                cost_result += costs[i] * usage_result[i]
        # If the usage is under the threshold, charge battery if needed.
        else:
            # If the current hour is one to be charged at, add the accompanying charge amount.
            """if (hour_charge := index_charge_amount.get(i)):
                # Extract at what position the current hour is amongst the indices.
                usage_result[i] = usage[i] + hour_charge
                cost_result += costs[i] * usage_result[i]
                bess.charge_bess(hour_charge)
            # If the current hour is not one to be charged at, use the grid.
            else:"""
            if not (hour_charge := index_charge_amount.get(i)):
                usage_result[i] = usage[i]
                cost_result += costs[i] * usage_result[i]
        i += 1
    return (cost_result, usage_result)


# ================================== SAVINGS CALCULATION ==========================================


# Calculates total cost for using the grid over 24 hours of usage.
def total_cost(costs: list, usage: list) -> float:
    hourly_cost = map(lambda x, y: x * y, costs, usage)
    return sum(hourly_cost)


# Prints of total cost, total cost with BESS and their comparison
def print_cost_comparison(total_cost: float, total_cost_bess: float):
    saved = total_cost - total_cost_bess
    percantage_saved = (saved / total_cost) * 100

    print("Total cost: " + str(round(total_cost, 2)) + " EUR")
    print("Total cost with BESS: " + str(round(total_cost_bess, 2)) + " EUR")
    print(str(round(saved, 2)) + " EUR is saved with a BESS",
          "which is " + str(round(percantage_saved, 2)) + "%")


# function: peak_shave_save
# Calculated how much money is saved by using peak shaving
# for a day.
# Parameters:
#   normal_usage    - the unaffected usage in mW - list[][]
#   new_usage       - the new, peak-shaved, usage in mW -  list[][]
#   effect_price    - price per kilowatt (kW) of the highest peak
# Returns:
#   The amount (in the unit passed) saved by using peak shaving for a time period
#   (a month is recommended since that is what energy companies use for billing).
def peak_shave_save(normal_usage: list, new_usage: list, effect_price: float) -> float:
    # assert same length
    assert (len(normal_usage) == len(new_usage))
    # get peaks from nested lists
    former_peak = max(map(max, normal_usage))
    new_peak = max(map(max, new_usage))
    # return diff times price
    return effect_price*(former_peak-new_peak)*1000


# Calculates daily savings during a given period using a BESS for peak shaving in energy prices.
def peak_shave_savings(week: int, start_day: int, end_day: int, bess: BESS) -> tuple:
    # Extract weekly usage and costs from example factory and Sundsvall.
    costs = data.get_elecricity_prices()
    usage = data.get_consumption()
    savings_per_day = []
    new_usage_hr = []

    total_savings = 0
    day = start_day
    # Loop through the given days and calculate savings per day and total savings.
    while (day <= end_day):
        #print(costs[week][day], usage[week][day])

        # NOTE temporary. Fill BESS before every day
        # bess.charge_bess(bess.availability - bess.available)

        peak_shave_cost, peak_shave_usage = peak_shaving(
            costs[week][day], usage[week][day], bess)
        # List of how much we save each day for energy prices. NOTE CAN WE PLOT THIS TO SEE WHY NEGATIVE???? NOT WRONG BUT STRANGE
        savings_per_day.append(total_cost(
            costs[week][day], usage[week][day]) - peak_shave_cost)
        # Total savings for a day
        total_savings += total_cost(costs[week][day],
                                    usage[week][day]) - peak_shave_cost

        # Add to total new usage
        new_usage_hr.append(peak_shave_usage)
        
        """ print(total_cost(costs[week][day], usage[week][day]))
        print(peak_shave_cost)
        print(total_savings)"""
        # print(bess)
        # plot_day(peak_shave_usage, usage[week][day])
        day += 1
    return (savings_per_day, total_savings, new_usage_hr)

# Call to get the information about how much is saved by
# the peak shaving algorithm (threshold-based)
def run_peak_save(former_usage, new_usage):
    # Taken from https://www.goteborgenergi.se/foretag/vara-nat/elnat/elnatsavgiften
    # 2022's prices
    EFFECT_PRICE = 4.49
    saved = peak_shave_save(former_usage, new_usage, EFFECT_PRICE)
    return round(saved, 2)


def run_all_weeks(bess: BESS) -> tuple:
    n_weeks = 3
    results = []
    tarriffs = []
    usage = data.get_consumption()
    # run for all weeks
    for i in range(0, n_weeks):
        # run for entire week
        results.append(peak_shave_savings(i, 0, 6, bess))
        tarriffs.append(run_peak_save(usage[i], results[i][2]))
    # Total saved for all three weeks
    total_savings_cost = sum(list(map(lambda elem: elem[1], results)))
    # Elongate over a year
    year_savings_costs = total_savings_cost * (52/n_weeks)
    tarriffs_year = sum(tarriffs) / len(tarriffs) * 12
    # return total savings and an example week
    return (round(year_savings_costs + tarriffs_year), (usage[0], results[0][2]))

# ================================= TESTING AND PLOTTING ==========================================

# Plots the usage of a day.
def plot_day(peak_shaving_usage: list, usage: list):
    x_points = np.array(range(24))

    plt.ylabel("Usage (MWh)")
    plt.xlabel("Hour")

    plt.plot(x_points, usage, color='r')
    plt.plot(x_points, peak_shaving_usage, color='g')

    plt.show()


# November 14th throughout 24 hours (in EUR/MWh).

# test_bess.charge_bess(test_bess.availability - test_bess.available)

"""# Peak shave algorithm results and BESS status.
peak_shave_cost, peak_shave_usage = peak_shaving(
    example_electric_costs, example_electric_usage, test_bess)

print(test_bess)

# Comparison between system with and without BESS.
print_cost_comparison(total_cost(example_electric_costs,
                      example_electric_usage), peak_shave_cost)

# Plot of usage with and without a BESS.
x_points = np.array(range(24))
y_points = peak_shave_usage

plt.ylabel("Usage (MWh)")
plt.xlabel("Hour")

plt.plot(x_points, example_electric_usage, color='r')   # Without BESS.
plt.plot(x_points, y_points, color='g')                 # With BESS.

plt.show()

#test_bess.charge_bess(test_bess.availability - test_bess.available)

# Calculate savings over a week
week = 0
a, b, new_usage = peak_shave_savings(week, 0, 6, test_bess)
print(a, b)


# Total savings for peak shaving (effekttariff)
peak_shave_saved = run_peak_save(data.get_consumption()[week], new_usage)"""

if __name__ == "__main__":

    # ======= NOT USED ========
    example_electric_costs = [34.94, 35.37, 37.15, 36.39, 37.16, 45.86, 99.82, 112.21, 172.49, 166.45,
                          142.40, 129.90, 105.33, 106.45, 99.93, 90.90, 90.02, 59.83, 40.62, 33.05, 28.34, 25.22, 21.38, 17.30]
    # First day of example factory in middle-Sweden (in MWh)
    example_electric_usage = [0.376, 0.360, 0.348, 0.368, 0.384, 0.608, 0.940, 1.200, 1.136, 1.128,
                            1.120, 1.088, 1.072, 1.104, 1.008, 0.952, 0.804, 0.696, 0.700, 0.664, 0.604, 0.628, 0.548, 0.364]
    # =========================

    # Test BESS initiation.
    test_bess = BESS(4, 0.1, 0.1, 0.9, 0.8, 1, SVK())
    test_bess.init_with_buffer()

    print("Total savings for a year:", run_all_weeks(test_bess))