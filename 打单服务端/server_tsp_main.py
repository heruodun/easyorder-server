import numpy as np

from server_tsp_io_helper import read_tsp_from_data, normalize
from server_tsp_neuron import generate_network, get_neighborhood, get_route
from server_tsp_distance import select_closest, euclidean_distance, route_distance
from server_tsp_plot import plot_network2, plot_route
import constants
from flask import current_app as app


# node_data (index, 经度, 纬度, address_id, 地址名称)
# todo 注意判断坐标是否合法
def run(dimension, nodes_data, diagrams_directory):

    print(nodes_data)

    coordinate_data, address_data = split_node_data(nodes_data)

    app.logger.info(f"request dimension {dimension} \ncoordinate_data {coordinate_data}, \naddress_data {address_data}")

    problem = read_tsp_from_data(dimension, coordinate_data)

    route = som(problem, 10000, diagrams_directory)

    detail_route = reorder_array(address_data, route, constants.START_ADDRESS_ID)

    print('Route found {}'.format(detail_route))

    problem = problem.reindex(route)

    print('Problem reindex {}'.format(route))

    distance = route_distance(problem)

    print('Route found of length {}'.format(distance))

    return detail_route


def reorder_array(array2, route, start_address_id):
    # 首先，找到开始地址ID对应的索引
    start_index = None
    for item in array2:
        if item[1] == start_address_id:
            start_index = item[0]
            break

    if start_index is None:
        return []  # 如果起始地址ID不存在，则返回空列表

    route_as_list = route.tolist()  # 将 pandas Index 转换为列表
    reordered = sorted(array2, key=lambda x: route_as_list.index(x[0]))

    # 最后，旋转列表确保以start_index开始
    # 找到start_index在reordered中的位置
    start_pos = 0
    for i, item in enumerate(reordered):
        if item[0] == start_index:
            start_pos = i
            break

    # 将列表旋转，以使start_index对应的元素出现在列表首位
    result_sequence = reordered[start_pos:] + reordered[:start_pos]

    return result_sequence


def split_node_data(node_data):
    # 初始化两个空数组用于存放拆分后的数据
    array1 = []  # 将存放(index, 经度, 纬度)
    array2 = []  # 将存放(index, address_id, 地址名称)

    # 遍历node_data数组中的每个元素
    for node in node_data:
        # 从原始元素中提取所有需要的字段
        index, longitude, latitude, address_id, place = node

        # 构建新的元组，并将它们添加到对应的数组中
        array1.append((index, longitude, latitude))
        array2.append((index, address_id, place, longitude, latitude))

    # 返回拆分后的两个数组
    return array1, array2


def som(problem, iterations, diagrams_directory, learning_rate=0.8):
    """Solve the TSP using a Self-Organizing Map."""

    # Obtain the normalized set of cities (w/ coord in [0,1])
    cities = problem.copy()

    cities[['x', 'y']] = normalize(cities[['x', 'y']])

    # The population size is 8 times the number of cities
    n = cities.shape[0] * 8

    # Generate an adequate network of neurons:
    network = generate_network(n)
    print('Network of {} neurons created. Starting the iterations:'.format(n))

    for i in range(iterations):
        if not i % 100:
            print('\t> Iteration {}/{}'.format(i, iterations), end="\r")
        # Choose a random city
        city = cities.sample(1)[['x', 'y']].values
        winner_idx = select_closest(network, city)
        # Generate a filter that applies changes to the winner's gaussian
        gaussian = get_neighborhood(winner_idx, n // 10, network.shape[0])
        # Update the network's weights (closer to the city)
        network += gaussian[:, np.newaxis] * learning_rate * (city - network)
        # Decay the variables
        learning_rate = learning_rate * 0.99997
        n = n * 0.9997

        # Check for plotting interval
        if not i % 1000:
            plot_network2(cities, network, name=diagrams_directory + '/{:05d}.png'.format(i))

        # Check if any parameter has completely decayed.
        if n < 1:
            print('Radius has completely decayed, finishing execution',
                  'at {} iterations'.format(i))
            break
        if learning_rate < 0.001:
            print('Learning rate has completely decayed, finishing execution',
                  'at {} iterations'.format(i))
            break
    else:
        print('Completed {} iterations.'.format(iterations))

    plot_network2(cities, network, name=diagrams_directory + '/final.png')

    route = get_route(cities, network)
    plot_route(cities, route, diagrams_directory + '/route.png')
    return route
