import numpy as np

def blockAverage_loop(data, blockSize):
    """
    对数据进行块平均处理
    :param data: 输入数据
    :param blockSize: 块大小
    :return: 平均后的数据
    """
    n = len(data)
    numBlocks = n // blockSize
    remainder = n % blockSize
    
    if numBlocks == 0:
        # 如果数据长度小于块大小，返回整个数据的平均值
        return np.mean(data)
    
    # 截断数据以适应完整的块
    truncatedData = data[:numBlocks * blockSize]
    reshapedData = truncatedData.reshape((numBlocks, blockSize))
    
    # 计算每个块的平均值
    averagedData = np.mean(reshapedData, axis=1)
    
    # 如果有余数，处理最后一个不完整的块
    if remainder != 0:
        lastBlock = data[numBlocks * blockSize:]
        lastAverage = np.mean(lastBlock)
        averagedData = np.append(averagedData, lastAverage)
    
    return averagedData

# 如果直接运行此脚本，则可以进行测试
if __name__ == "__main__":
    # 示例调用（实际使用时请提供正确的数据）
    # data = np.random.rand(100)
    # result = blockAverage_loop(data, 10)
    pass
