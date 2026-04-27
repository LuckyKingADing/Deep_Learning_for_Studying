import matplotlib.pyplot as plt
from readgnsscsv import readgnsscsv

def plotgnsscsv():
    """
    绘制GNSS数据图表
    """
    plt.close('all')  # 关闭所有图形
    gnss = readgnsscsv('D:/dockers/test/20250906_shanghaizhan/gnss.csv', list(range(1, 18)))  # 1:17 对应Python中的range(1, 18)
    t0 = gnss[0, 1]  # 第2列（索引1）
    
    plt.plot(gnss[:, 1] - t0, gnss[:, 16], '.r-')  # 第17列（索引16）
    plt.show()

# 如果直接运行此脚本，则执行plotgnsscsv函数
if __name__ == "__main__":
    plotgnsscsv()
