def skipCommentLines(fid):
    """
    跳过注释行
    :param fid: 文件句柄
    """
    import io
    
    while True:
        # 记录当前位置
        pos = fid.tell()
        
        # 读取一行
        line = fid.readline()
        
        # 如果到达文件末尾，则退出
        if not line:
            break
            
        # 去除行尾换行符
        line = line.rstrip('\n\r')
        
        # 如果是空行，继续下一行
        if not line:
            continue
        
        # 检查第一字符是否为数字
        if line[0].isdigit():
            # 回退到上一行的位置
            fid.seek(pos)
            break
