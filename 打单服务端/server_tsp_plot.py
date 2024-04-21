import matplotlib.pyplot as plt
import matplotlib as mpl


def plot_network(cities, neurons, name='diagram.png', ax=None):
    """Plot a graphical representation of the problem"""
    mpl.rcParams['agg.path.chunksize'] = 10000

    if not ax:
        fig = plt.figure(figsize=(5, 5), frameon=False)
        axis = fig.add_axes([0, 0, 1, 1])

        axis.set_aspect('equal', adjustable='datalim')
        plt.axis('off')

        axis.scatter(cities['x'], cities['y'], color='red', s=4)
        axis.plot(neurons[:, 0], neurons[:, 1], 'r.', ls='-', color='#0063ba', markersize=2)

        plt.savefig(name, bbox_inches='tight', pad_inches=0, dpi=200)
        plt.close()

    else:
        ax.scatter(cities['x'], cities['y'], color='red', s=4)
        ax.plot(neurons[:, 0], neurons[:, 1], 'r.', ls='-', color='#0063ba', markersize=2)
        return ax


def plot_network2(cities, neurons, name='diagram.png', ax=None):
    """Plot a graphical representation of the problem with smaller indices"""
    mpl.rcParams['agg.path.chunksize'] = 10000
    if not ax:
        fig = plt.figure(figsize=(5, 5), frameon=False)
        axis = fig.add_axes([0, 0, 1, 1])
        axis.set_aspect('equal', adjustable='datalim')
        plt.axis('off')

        # 绘制城市点
        axis.scatter(cities['x'], cities['y'], color='red', s=4)
        # 绘制路径
        axis.plot(neurons[:,0], neurons[:,1], 'r.', ls='-', color='#0063ba', markersize=2)

        # 在每个城市旁边添加较小的索引
        for i, txt in enumerate(cities.index):
            axis.annotate(txt, (cities['x'].iloc[i], cities['y'].iloc[i]),
                          textcoords="offset points",
                          xytext=(0, 5),
                          ha='center',
                          fontsize=6)  # 调整字体大小

        plt.savefig(name, bbox_inches='tight', pad_inches=0, dpi=200)
        plt.close()
    else:
        ax.scatter(cities['x'], cities['y'], color='red', s=4)
        ax.plot(neurons[:,0], neurons[:,1], 'r.', ls='-', color='#0063ba', markersize=2)

        # 在每个城市旁边添加较小的索引
        for i, txt in enumerate(cities.index):
            ax.annotate(txt, (cities['x'].iloc[i], cities['y'].iloc[i]),
                        textcoords="offset points",
                        xytext=(0, 5),
                        ha='center',
                        fontsize=6)  # 调整字体大小

        return ax


def plot_route(cities, route, name='diagram.png', ax=None):
    """Plot a graphical representation of the route obtained"""
    mpl.rcParams['agg.path.chunksize'] = 10000

    if not ax:
        fig = plt.figure(figsize=(5, 5), frameon=False)
        axis = fig.add_axes([0, 0, 1, 1])

        axis.set_aspect('equal', adjustable='datalim')
        plt.axis('off')

        axis.scatter(cities['x'], cities['y'], color='red', s=4)
        route = cities.reindex(route)
        route.loc[route.shape[0]] = route.iloc[0]
        axis.plot(route['x'], route['y'], color='purple', linewidth=1)

        plt.savefig(name, bbox_inches='tight', pad_inches=0, dpi=200)
        plt.close()

    else:
        ax.scatter(cities['x'], cities['y'], color='red', s=4)
        route = cities.reindex(route)
        route.loc[route.shape[0]] = route.iloc[0]
        ax.plot(route['x'], route['y'], color='purple', linewidth=1)
        return ax
