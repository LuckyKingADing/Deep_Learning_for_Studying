from plot_skyview import plot_skyview

def skyplot():
    """
    绘制天空图
    """
    filename = '/mnt/d/dockers/sky.txt'
    plot_skyview(filename)

# 如果直接运行此脚本，则执行skyplot函数
if __name__ == "__main__":
    skyplot()