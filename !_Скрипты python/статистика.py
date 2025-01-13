import statistics  as st
data = [1, 2, 3, 4, 5]

print("Выборочная дисперсия данных: ",st.variance(data))
print("Выборочное стандартное отклонение данных  ",st. stdev(data))
print("Дисперсия данных по популяции:  ",st .pvariance(data))
print("Стандартное отклонени данных по популяции: ",st.pstdev(data))