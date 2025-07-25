def excel_filter(array, condition_func):
    """
    模拟Excel的FILTER函数。
    :param array: 可迭代对象（如列表）
    :param condition_func: 用于筛选的函数，返回True则保留该元素
    :return: 满足条件的元素列表
    """
    return [item for item in array if condition_func(item)]

# 示例用法
data = [10, 25, 30, 45, 50]
# 过滤出大于30的元素
filtered = excel_filter(data, lambda x: x > 30)
print(filtered)  # 输出: [45, 50]
