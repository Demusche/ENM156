def total_cost(costs, usage) -> float:
    hourly_cost = map(lambda x, y: x * y, costs, usage)
    return sum(hourly_cost)


print(total_cost([1, 2, 3, 4], [2, 2, 2, 2]))