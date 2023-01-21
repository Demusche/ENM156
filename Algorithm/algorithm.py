import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from DataHandling.SVK_data import SVK_data as SVK
from Algorithm.fcr import BESS
import numpy as np
import matplotlib.pyplot as plt
# from openmeteo_py import Hourly, Daily, Options, OWmanager   # Get Forecasting


def test_case(prices):
    return np.random.shuffle(prices)


def remove_spikes_test(usage_day_before, usage):
    bess_output = 0
    avg = np.mean(usage_day_before)
    if (usage > avg):
        bess_output = avg - usage
    else:
        bess_output = avg - usage
    print(bess_output)
    return bess_output


def remove_spikes_day_test(usage_day_before, usage_day):
    energy_usage = [0] * len(usage_day)
    for i in range(len(usage_day)):
        energy_usage[i] = remove_spikes_test(usage_day_before, usage_day[i])
        print(energy_usage[i])
    return energy_usage

# if usage above last days mean use battery otherwise charge it
def lower_max_usage_unused(prices, usage_day_before, usage, bess):
    avg = np.mean(usage_day_before)
    for i in range(len(usage_day_before)):
        if (usage[i] > avg):
            use_battery(i, prices[i])
        else:
            charge_battery(i, prices[i])

# use battery if the change in usage i higher than some threshold
def lower_usage_change_spikes(prices_day, usage_day, capacity, change_threshold):
    change = 0
    i = 1
    while (i < len(usage_day)-1):
        change = (usage_day[i] / usage_day[i-1]) - 1
        if (change > change_threshold):
            usage_day[i] = usage_day[i] - capacity/6
            usage_day[i+1] = usage_day[i+1] - capacity/3
            usage_day[i+2] = usage_day[i+2] - capacity/3
            usage_day[i+3] = usage_day[i+3] - capacity/6
            #use_battery(i, prices_day[i+1])
            i = i + 4
        elif (change < -change_threshold):
            usage_day[i] = usage_day[i] + 2*capacity/3
            usage_day[i+1] = usage_day[i+1] + capacity/3
            i = i + 2
        else:
           # use_grid(i, prices_day[i+1])
            i = i
        i = i + 1
    return usage_day


# Peak shaving throughout a day, with focus on charging on the cheapest hours.
def peak_shaving(costs: list, usage: list, bess: BESS):
    # Calculate threshold for active hours.
    threshold = get_threshold(usage, bess)
    print(threshold)
    # Extract at what hours to charge and how much.
    index_charge_amount = get_charging_hours(costs, usage, threshold, bess)
    # Create array of size usage.
    usage_result = [0]*len(usage)
    cost_result = 0
    i = 0
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
            if (hour_charge := index_charge_amount.get(i)):
                # Extract at what position the current hour is amongst the indices.
                usage_result[i] = usage[i] + hour_charge
                cost_result += costs[i] * usage_result[i]
                bess.charge_bess(hour_charge)
            # If the current hour is not one to be charged at, use the grid.
            else:
                usage_result[i] = usage[i]
                cost_result += costs[i] * usage_result[i]
        i += 1
    return (cost_result, usage_result)


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
def peak_shave_save(normal_usage: list, new_usage: list, effect_price: float):
    # assert same length
    assert (len(normal_usage) == len(new_usage))
    # get peaks from nested lists
    former_peak = max(map(max, normal_usage))
    new_peak = max(map(max, new_usage))
    # return diff times price
    return effect_price*(former_peak-new_peak)*1000

# Calculates total cost for using the grid over 24 hours of usage.
def total_cost(prices, usage):
    cost = 0
    i = 0
    while i < len(usage) - 1:
        cost += prices[i] * usage[i]
        i += 1
    return cost

# Extracts the active hours of a working day.
def get_active_hours_index(usage: list):
    # Adding 0.0005 to round up with 3 decimals.
    avg = round((sum(usage) / len(usage)) + 0.0005, 3)
    # Get start- and stop index of active period.
    above_avg = list(filter(lambda x: x > avg, usage))
    start_index = usage.index(above_avg[0])
    end_index = (len(usage) - 1) - list(reversed(usage)).index(above_avg[-1])
    return (start_index, end_index)


def get_active_hours(usage: list):
    start_index, end_index = get_active_hours_index(usage)
    return usage[start_index: end_index + 1]


# Calculates total usage during active hours.
def get_usage_active(usage: list):
    active_hours = get_active_hours(usage)
    return sum(active_hours)

# Calculates the upper threshold.
#   Find the total consumption during active hours
#   Compare to BESS available amount when entering active period
#   Total consumption - available from BESS = what is needed from grid
#   Divide what is needed from grid by number of hours of active period
#   to get threshold for active period
def get_threshold(usage: list, bess):
    active_hours = get_active_hours(usage)
    return (sum(active_hours) - bess.availability) / len(active_hours)

# Extracts what hours to be charged on with a specified amount during inactive hours.
def get_charging_hours(costs: list, usage: list, threshold: float, bess: BESS):
    # Map index and usage to cost.
    index_cost_usage = list(zip(range(0, len(costs)), costs, usage))
    # Check on which part of the day that the inactive hours aren't.
    start_index, end_index = get_active_hours_index(usage)
    inactive_hours_w_index = index_cost_usage[0:start_index] + index_cost_usage[end_index+1:]
    # Sort the mapped values after cost from lowest to highest.
    sorted_costs = sorted(inactive_hours_w_index, key=lambda t: t[1])
    # Calculate charge amount to handle the peak shaving of active hours.
    tot_charge_req = bess.availability - bess.available
    index_charge_amount = dict()
    new_charge = 0
    index = 0
    # Extract what hours that should be charged on to fully charge for as cheap as possible.
    while(new_charge < tot_charge_req):
        usage_cheapest = sorted_costs[index][2]
        # Find bottleneck of charge for the hour.
        # Charge min(bess.power, usage_during_cheapest - threshold, required charge)
        added_charge = min(bess.power, threshold - usage_cheapest, tot_charge_req - new_charge)
        new_charge += added_charge
        # Add hour to be charged at to the indices and the amount to be charged at that time.
        index_charge_amount[sorted_costs[index][0]] = added_charge
        index += 1
    print(index_charge_amount.values())
    return index_charge_amount

# Finds the lowest priced hours to charge battery to full availability.
def charge_during_lowtime(costs: list, usage: list, bess: BESS, threshold: float):
    charge_costs = 0
    # Find total charge required
    tot_charge_req = bess.availability - bess.available
    # Map costs to usage
    costs_map_usage = zip(costs, usage)
    # Remove active hours from costs (NOT IN-PLACE)
    start_index, end_index = get_active_hours_index(usage)
    costs_map_usage = costs_map_usage[0:start_index].extend(
        costs_map_usage[end_index+1:])
    # sort costs-array (NOT IN-PLACE)
    cheapest_hours = sorted(costs_map_usage, key=lambda tup: tup[0])
    # Check if total charge required is 0 (fulfilled)
    index = 0
    while (bess.available < bess.availability):
        costs_cheapest = cheapest_hours[index][0]
        usage_cheapest = cheapest_hours[index][1]
        # Charge min(bess.power, usage_during_cheapest - threshold, required charge)
        added_charge = min(bess.power, threshold -
                           usage_cheapest, bess.availability - bess.available)
        bess.charge(added_charge)
        # assertion
        assert (bess.charge <= bess.capacity*bess.max_charge)
        charge_costs += added_charge * costs_cheapest
        index += 1
        # If cannot fill during inactive hours
        if (index >= len(cheapest_hours)):
            return total_cost
    # Good to go (calculate total cost perchance)
    return total_cost


# November 14th throughout 24 hours (in EUR/MWh).
example_electric_costs = [34.94, 35.37, 37.15, 36.39, 37.16, 45.86, 99.82, 112.21, 172.49, 166.45,
                          142.40, 129.90, 105.33, 106.45, 99.93, 90.90, 90.02, 59.83, 40.62, 33.05, 28.34, 25.22, 21.38, 17.30]

# First day of example factory in middle-Sweden (in MWh)
example_electric_usage = [0.376, 0.360, 0.348, 0.368, 0.384, 0.608, 0.940, 1.200, 1.136, 1.128,
                          1.120, 1.088, 1.072, 1.104, 1.008, 0.952, 0.804, 0.696, 0.700, 0.664, 0.604, 0.628, 0.548, 0.364]


# Prints of total cost, total cost with BESS and their comparison
def print_cost_comparison(total_cost, total_cost_bess):
    saved = total_cost - total_cost_bess
    percantage_saved = (saved / total_cost) * 100

    print("Total cost: " + str(round(total_cost, 2)) + " EUR")
    print("Total cost with BESS: " + str(round(total_cost_bess, 2)) + " EUR")
    print(str(round(saved, 2)) + " EUR is saved with a BESS",
          "which is " + str(round(percantage_saved, 2)) + "%")


# Price arbitrage with battery capacity of 1 hour with 1 hour look-ahead.
def price_arbitrage(costs=example_electric_costs):
    time = 0
    total_cost = 0
    total_cost_bess = 0

    # Iteration through 24 hours with responses to prices.
    while time < (len(costs) - 1):
        cost_now = costs[time]
        cost_next = costs[time + 1]
        # If cheaper now than next hour, charge battery and use in the following hour.
        if (cost_now < cost_next):
            print("At time " + str(time), "buy at cost " +
                  str(cost_now) + " EUR/MWh")
            print("At time " + str(time + 1),
                  "use battery at cost " + str(cost_next) + " EUR/MWh")
            total_cost += cost_now + cost_next
            total_cost_bess += 2 * cost_now
            time += 1
        # Otherwise, use power grid at current cost.
        else:
            print("At time " + str(time), "use power grid at cost " +
                  str(cost_now) + " EUR/MWh")
            total_cost += cost_now
            total_cost_bess += cost_now
        time += 1

    print_cost_comparison(total_cost, total_cost_bess)


# Price arbitrage with battery capacity of 1 hour with 1 hour look-ahead, weighted with usage.
def price_arbitrage_weighted_1(costs=example_electric_costs, usage=example_electric_usage):
    time = 0
    total_cost = 0
    total_cost_bess = 0

    # Iteration through 24 hours with responses to prices with amount used.
    while time < (len(costs) - 1):
        cost_now = costs[time]
        cost_next = costs[time + 1]
        usage_now = usage[time]
        usage_next = usage[time + 1]
        total_cost_now = cost_now * usage_now
        total_cost_next = cost_next * usage_next
        # If, accounted for usage, it's cheaper now than next hour, charge battery and use in the following hour.
        if (total_cost_now < total_cost_next):
            print("At time " + str(time), "buy at cost " +
                  str(total_cost_now) + " EUR")
            print("At time " + str(time + 1), "use battery at cost " +
                  str(total_cost_next) + " EUR")
            total_cost += total_cost_now + total_cost_next
            total_cost_bess += 2 * total_cost_now
            time += 1
        # Otherwise, use power grid at current cost.
        else:
            print("At time " + str(time), "use power grid at cost " +
                  str(round(total_cost_now)) + " EUR")
            total_cost += total_cost_now
            total_cost_bess += total_cost_now
        time += 1

    print_cost_comparison(total_cost, total_cost_bess)


# Print what cost and at what time to charge the battery
def charge_battery(time, cost):
    print(f"At time {time} buy at cost {round(cost, 3)} EUR")


# Print what cost and at what time to use the battery
def use_battery(time, cost):
    print(f"At time {time} use battery at cost {round(cost, 3)} EUR")


# Print what cost and at what time to use the power grid
def use_grid(time, cost):
    print(f"At time {time} use power grid at cost {round(cost, 3)} EUR")

# Vaskad, jobbigt att räkna tid, cirkulärt it is
# Price arbitrage with battery capacity of 2 hours with 3 hour look-ahead, weighted with usage.
def price_arbitrage_weighted_2(costs=example_electric_costs, usage=example_electric_usage):
    time = 0
    total_cost = 0
    total_cost_bess = 0
    look_ahead = 3

    # Iteration through 24 hours with responses to prices with amount used.
    while time < (len(costs) - look_ahead):
        total_cost_0 = costs[time] * usage[time]
        total_cost_1 = costs[time + 1] * usage[time + 1]
        total_cost_2 = costs[time + 2] * usage[time + 2]
        total_cost_3 = costs[time + 3] * usage[time + 3]
        # If, accounted for usage, it's cheaper now than the following hours, charge battery and use in the following hours/hour.
        if (total_cost_0 > total_cost_1):
            use_grid(time, total_cost_0)
            total_cost_bess += total_cost_0
            time += 1
        elif (total_cost_1 > total_cost_2):
            charge_battery(time, total_cost_0)
            use_battery(time + 1, total_cost_1)
            total_cost_bess += 2 * total_cost_0
            time += 2
        elif (total_cost_2 > total_cost_3):
            charge_battery(time, total_cost_0)
            use_grid(time + 1, total_cost_1)
            use_battery(time + 2, total_cost_2)
            total_cost_bess += 2 * total_cost_0 + total_cost_1
            time += 3
        else:
            charge_battery(time, total_cost_0)
            charge_battery(time + 1, total_cost_1)
            use_battery(time + 2, total_cost_2)
            use_battery(time + 3, total_cost_3)
            total_cost_bess += 2 * total_cost_0 + 2 * total_cost_1
            time += 4
        total_cost(costs, usage)


# Retrieves the cost per hour for a set number of hours
def hourly_costs(now, look_ahead, costs, usage):
    cost_for_hour = [None for _ in range(look_ahead + 1)]
    for i in range(look_ahead + 1):
        cost_for_hour[i] = costs[(now + i) % 24] * usage[(now + i) % 24]
    return cost_for_hour


# Calculates throughout a 24 hour span with vision on the following day.
def price_arbitrage_circular(costs, usage):
    time = 0
    # Hardcoded algorithm for this size atm.
    LOOK_AHEAD = 3
    total_cost_bess = 0
    # Circular iteration through 24 hours with vision on the next 3 hours of following day.
    while time < (len(costs)):
        cost_for_hour = hourly_costs(time, LOOK_AHEAD, costs, usage)
        # Hour 0 is more expensive than hour 1.
        if (cost_for_hour[0] > cost_for_hour[1]):
            use_grid(time, cost_for_hour[0])
            total_cost_bess += cost_for_hour[0]
            time += 1
            continue
        # Hour 0 is cheaper than hour 1.
        else:
            charge_battery(time, cost_for_hour[0])
            time += 1

        if (time == 23):
            total_cost_bess += cost_for_hour[0]
            break

        # Hour 1 is more expensive than hour 2.
        if (cost_for_hour[1] > cost_for_hour[2]):
            use_battery(time + 1, cost_for_hour[1])
            total_cost_bess += 2 * cost_for_hour[0]
            time += 1
            continue
        # Hour 1 is cheaper than hour 2.
        else:
            # Hour 1 is more expensive than hour 3.
            if (cost_for_hour[1] > cost_for_hour[3]):
                use_grid(time + 1, cost_for_hour[1])
                use_battery(time + 2, cost_for_hour[2])
                total_cost_bess += 2 * cost_for_hour[0] + cost_for_hour[1]
                time += 2
            # Hour 1 is cheaper than hour 3.
            else:
                charge_battery(time + 1, cost_for_hour[1])
                use_battery(time + 2, cost_for_hour[2])
                use_battery(time + 3, cost_for_hour[3])
                time += 3
    print_cost_comparison(total_cost(costs, usage), total_cost_bess)


# BESS with a specified capacity (MWh), buffer size (%), depth of discharge (%), charge of battery (MWh), buffer that must be maintained for an emergency (MWh), maximum available amount (MWh) and a currently available amount to be used (MWh).
class Bess:
    # Initial available buffer and amount to be used is 0.
    def __init__(self, capacity, buffer_size, dod):
        self.capacity = capacity
        self.buffer_size = buffer_size
        self.dod = dod
        self.charge = 0
        self.buffer = 0
        # Availability is decided by how big the buffer size and depth of discharge is.
        self.availability = capacity - \
            (capacity * (max(100 - dod, buffer_size) / 100))
        self.available = 0

    def __str__(self):
        return f"Capacity: {self.capacity}MWh, Buffer size: {round(100 * self.buffer_size, 3)}%, Depth of discharge: {round(self.dod, 3)}%, Total charge: {round(self.charge, 3)} MWh, Buffer: {round(self.buffer, 3)}MWh, Available: {round(self.available, 3)}MWh"

    def init_with_buffer(self):
        self.buffer = self.capacity * self.buffer_size
        self.charge = self.capacity * self.buffer_size

    def enough_available_amount(self, amount_needed):
        return self.available <= amount_needed

    def charge_bess(self, amount):
        if (self.charge + amount <= self.capacity):
            self.charge += amount
            self.available = self.charge - self.buffer_size * self.capacity
            self.buffer = self.charge - self.available

    def discharge_bess(self, amount):
        if (self.available >= amount):
            self.charge -= amount
            self.available = self.charge - self.buffer_size * self.capacity
            self.buffer = self.charge - self.available


# Calculates price arbitrage for 24 hours with electric cost, usage, frequency regulation etc with best hourly course of action.
def bess_optimiser(electric_costs, daily_usage, freq_reg_values, bess):
    time = 0
    # Hardcoded for now.
    LOOK_AHEAD = 3
    total_cost_bess = 0
    while time < len(electric_costs) - LOOK_AHEAD:
        hourly_electric_costs = hourly_costs(
            time, LOOK_AHEAD, electric_costs, daily_usage)


# price_arbitrage()
# print()
# price_arbitrage_weighted_1()
# print()
#price_arbitrage_circular(example_electric_costs, example_electric_usage)
# print()

test_bess = BESS(4, 0.1, 0.1, 0.9, 0.8, 1, SVK())
test_bess.init_with_buffer()
#test_bess.charge_bess(test_bess.availability - test_bess.available)


peak_shave_cost, peak_shave_usage = peak_shaving(example_electric_costs, example_electric_usage, test_bess)

print_cost_comparison(total_cost(example_electric_costs, example_electric_usage), peak_shave_cost)

#print(f"{test_bess.availability}MWh availability")
# print(example_electric_usage)
xpoints = np.array(range(24))
plt.plot(xpoints, example_electric_usage, color='r')
ypoints = peak_shave_usage

print(test_bess)
plt.ylabel("Usage (MWh)")
plt.xlabel("Hour")
plt.plot(xpoints, ypoints, color='g')

plt.show()

fig, axs = plt.subplots(1)
axs.set_title(f"Usage during a day")
axs.set_ylabel(f"Usage (MWh)")
axs.set_xlabel(f"Time (h)")
plt.plot(xpoints, example_electric_usage, color='r')

fig, axs = plt.subplots(1)
axs.set_title(f"Electric costs during a day")
axs.set_ylabel(f"Costs (EUR/MWh)")
axs.set_xlabel(f"Time (h)")
plt.plot(xpoints, example_electric_costs, color='g')

cost_for_hour = [None for _ in range(24)]
for i in range(24):
    cost_for_hour[i] = example_electric_costs[i] * example_electric_usage[i]

fig, axs = plt.subplots(1)
axs.set_title(f"Costs during a day")
axs.set_ylabel(f"Costs (EUR)")
axs.set_xlabel(f"Time (h)")
plt.plot(xpoints, cost_for_hour, color='g')

# plt.show()


# Call to get the information about how much is saved by
# the peak shaving algorithm (threshold-based)
def run_peak_save(former_usage, new_usage):
    # Taken from https://www.goteborgenergi.se/foretag/vara-nat/elnat/elnatsavgiften
    # 2022's prices
    EFFECT_PRICE = 49.3
    saved = peak_shave_save(former_usage, new_usage, EFFECT_PRICE)
    print("Peak shaving algorithm saved: ", round(saved, 2), "sek")


run_peak_save([example_electric_usage], [ypoints])
