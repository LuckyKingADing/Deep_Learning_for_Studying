import numpy as np
import matplotlib.pyplot as plt
from calculate_errors import calculate_errors


def plot_errors(common_timelc, diff_datalc, common_timetc, diff_datatc, common_timegnss, diff_datagnss, t0, save_path, yaw, t_start=None, t_end=None, lcver='LC', tcver='TC', is_detail=False, plotlc=True, plottc=True, gap_intervals=None):
    """
    PLOT_ERRORS 绘制误差曲线
    :param common_timelc: LC时间向量
    :param diff_datalc: LC差值数据
    :param common_timetc: TC时间向量
    :param diff_datatc: TC差值数据
    :param common_timegnss: GNSS时间向量
    :param diff_datagnss: GNSS差值数据
    :param t0: 时间基准点
    :param save_path: 图像保存路径
    :param t_start: 时间范围起始点（可选），绝对时间
    :param t_end: 时间范围结束点（可选），绝对时间
    :param lcver: LC版本标识
    :param tcver: TC版本标识
    :param is_detail: 是否为详细子图模式（详细子图不减去t0）
    :param plotlc: 是否绘制LC数据
    :param plottc: 是否绘制TC数据
    :param gap_intervals: gap区间列表，List[Tuple[float, float]]，GPS秒为单位
                            落在gap区间内的误差值会被替换为10
    """
    # 判断是否只绘制GNSS
    only_gnss = not plotlc and not plottc
    
    # 创建第一个图形窗口
    fig1, axes1 = plt.subplots(4, 1, figsize=(12, 16))
    if only_gnss:
        fig1.suptitle('Error Analysis (GNSS Only)', fontsize=16)
    else:
        fig1.suptitle('Error Analysis (With GNSS)', fontsize=16)
    
    # 如果是详细子图模式，设置x轴刻度格式为显示完整数值
    if is_detail:
        for ax in axes1:
            ax.ticklabel_format(style='plain', axis='x', useOffset=False)

    # 计算各种误差
    # 根据是否为详细子图模式决定是否减去t0
    if is_detail:
        # 详细子图模式：不减去t0
        time_offset = 0
        # 筛选时使用绝对时间
        time_filter_offset = 0
    else:
        # 普通模式：减去t0
        time_offset = t0
        # 筛选时也需要减去t0
        time_filter_offset = t0
    
    # LC误差
    if common_timelc is not None and diff_datalc is not None and len(common_timelc) > 0 and len(diff_datalc) > 0:
        lc_horizontal, lc_lateral, lc_vertical, lc_forward = calculate_errors(diff_datalc, yaw)
        time_lc = common_timelc - time_offset

        # 根据时间范围筛选数据
        if t_start is not None and t_end is not None and len(t_start) > 0 and len(t_end) > 0:
            # 处理向量形式的时间范围
            if np.isscalar(t_start) and np.isscalar(t_end):
                # 单个时间范围
                lc_indices = np.where((time_lc >= t_start - time_filter_offset) & (time_lc <= t_end - time_filter_offset))[0]
            elif isinstance(t_start, (list, np.ndarray)) and isinstance(t_end, (list, np.ndarray)) and len(t_start) == len(t_end):
                # 多个时间范围，合并所有范围内的数据
                valid_indices = []
                for i in range(len(t_start)):
                    indices = np.where((time_lc >= t_start[i] - time_filter_offset) & (time_lc <= t_end[i] - time_filter_offset))[0]
                    valid_indices.extend(indices)
                # 去除重复的索引并排序
                lc_indices = np.unique(valid_indices)
            else:
                # 不支持的时间范围格式，跳过筛选
                lc_indices = np.arange(len(time_lc))

            if len(lc_indices) > 0:
                time_lc = time_lc[lc_indices]
                lc_horizontal = lc_horizontal[lc_indices]
                lc_lateral = lc_lateral[lc_indices]
                lc_vertical = lc_vertical[lc_indices]
                lc_forward = lc_forward[lc_indices]
                # gap 区间内填充固定值 10
                if gap_intervals is not None and len(gap_intervals) > 0 and len(time_lc) > 0:
                    for start, end in gap_intervals:
                        for i in range(len(time_lc)):
                            if start <= time_lc[i] <= end:
                                lc_horizontal[i] = 10.0
                                lc_lateral[i] = 10.0
                                lc_vertical[i] = 10.0
                                lc_forward[i] = 10.0
            else:
                # 如果没有数据在时间范围内，清空数据
                time_lc = np.array([])
                lc_horizontal = np.array([])
                lc_lateral = np.array([])
                lc_vertical = np.array([])
                lc_forward = np.array([])
    else:
        # 如果LC数据为空，初始化为空数组
        time_lc = np.array([])
        lc_horizontal = np.array([])
        lc_lateral = np.array([])
        lc_vertical = np.array([])
        lc_forward = np.array([])

    # TC误差
    if common_timetc is not None and diff_datatc is not None and len(common_timetc) > 0 and len(diff_datatc) > 0:
        tc_horizontal, tc_lateral, tc_vertical, tc_forward = calculate_errors(diff_datatc, yaw)
        time_tc = common_timetc - time_offset

        # 根据时间范围筛选数据
        if t_start is not None and t_end is not None and len(t_start) > 0 and len(t_end) > 0:
            # 处理向量形式的时间范围
            if np.isscalar(t_start) and np.isscalar(t_end):
                # 单个时间范围
                tc_indices = np.where((time_tc >= t_start - time_filter_offset) & (time_tc <= t_end - time_filter_offset))[0]
            elif isinstance(t_start, (list, np.ndarray)) and isinstance(t_end, (list, np.ndarray)) and len(t_start) == len(t_end):
                # 多个时间范围，合并所有范围内的数据
                valid_indices = []
                for i in range(len(t_start)):
                    indices = np.where((time_tc >= t_start[i] - time_filter_offset) & (time_tc <= t_end[i] - time_filter_offset))[0]
                    valid_indices.extend(indices)
                # 去除重复的索引并排序
                tc_indices = np.unique(valid_indices)
            else:
                # 不支持的时间范围格式，跳过筛选
                tc_indices = np.arange(len(time_tc))

            if len(tc_indices) > 0:
                time_tc = time_tc[tc_indices]
                tc_horizontal = tc_horizontal[tc_indices]
                tc_lateral = tc_lateral[tc_indices]
                tc_vertical = tc_vertical[tc_indices]
                tc_forward = tc_forward[tc_indices]
                # gap 区间内填充固定值 10
                if gap_intervals is not None and len(gap_intervals) > 0 and len(time_tc) > 0:
                    for start, end in gap_intervals:
                        for i in range(len(time_tc)):
                            if start <= time_tc[i] <= end:
                                tc_horizontal[i] = 10.0
                                tc_lateral[i] = 10.0
                                tc_vertical[i] = 10.0
                                tc_forward[i] = 10.0
            else:
                # 如果没有数据在时间范围内，清空数据
                time_tc = np.array([])
                tc_horizontal = np.array([])
                tc_lateral = np.array([])
                tc_vertical = np.array([])
                tc_forward = np.array([])
    else:
        # 如果TC数据为空，初始化为空数组
        time_tc = np.array([])
        tc_horizontal = np.array([])
        tc_lateral = np.array([])
        tc_vertical = np.array([])
        tc_forward = np.array([])

    # GNSS误差
    if common_timegnss is not None and diff_datagnss is not None and len(common_timegnss) > 0 and len(diff_datagnss) > 0:
        gnss_horizontal, gnss_lateral, gnss_vertical, gnss_forward = calculate_errors(diff_datagnss, yaw)
        time_gnss = common_timegnss - time_offset

        # 根据时间范围筛选数据
        if t_start is not None and t_end is not None and len(t_start) > 0 and len(t_end) > 0:
            # 处理向量形式的时间范围
            if np.isscalar(t_start) and np.isscalar(t_end):
                # 单个时间范围
                gnss_indices = np.where((time_gnss >= t_start - time_filter_offset) & (time_gnss <= t_end - time_filter_offset))[0]
            elif isinstance(t_start, (list, np.ndarray)) and isinstance(t_end, (list, np.ndarray)) and len(t_start) == len(t_end):
                # 多个时间范围，合并所有范围内的数据
                valid_indices = []
                for i in range(len(t_start)):
                    indices = np.where((time_gnss >= t_start[i] - time_filter_offset) & (time_gnss <= t_end[i] - time_filter_offset))[0]
                    valid_indices.extend(indices)
                # 去除重复的索引并排序
                gnss_indices = np.unique(valid_indices)
            else:
                # 不支持的时间范围格式，跳过筛选
                gnss_indices = np.arange(len(time_gnss))

            if len(gnss_indices) > 0:
                time_gnss = time_gnss[gnss_indices]
                gnss_horizontal = gnss_horizontal[gnss_indices]
                gnss_lateral = gnss_lateral[gnss_indices]
                gnss_vertical = gnss_vertical[gnss_indices]
                gnss_forward = gnss_forward[gnss_indices]
                # gap 区间内填充固定值 10
                if gap_intervals is not None and len(gap_intervals) > 0 and len(time_gnss) > 0:
                    for start, end in gap_intervals:
                        for i in range(len(time_gnss)):
                            if start <= time_gnss[i] <= end:
                                gnss_horizontal[i] = 10.0
                                gnss_lateral[i] = 10.0
                                gnss_vertical[i] = 10.0
                                gnss_forward[i] = 10.0
            else:
                # 如果没有数据在时间范围内，清空数据
                time_gnss = np.array([])
                gnss_horizontal = np.array([])
                gnss_lateral = np.array([])
                gnss_vertical = np.array([])
                gnss_forward = np.array([])
    else:
        # 如果GNSS数据为空，初始化为空数组
        time_gnss = np.array([])
        gnss_horizontal = np.array([])
        gnss_lateral = np.array([])
        gnss_vertical = np.array([])
        gnss_forward = np.array([])

    # 绘制水平误差（第一行）
    axes1[0].grid(True)
    # 调整绘图顺序，如果画了gnss，就画在第一个
    if len(time_gnss) > 0 and len(gnss_horizontal) > 0:
        axes1[0].plot(time_gnss, gnss_horizontal, '-o', linewidth=1.5, markersize=2, label='GNSS')
    if len(time_lc) > 0 and len(lc_horizontal) > 0:
        axes1[0].plot(time_lc, lc_horizontal, '-s', linewidth=1.5, markersize=2, label=lcver)
    if len(time_tc) > 0 and len(tc_horizontal) > 0:
        axes1[0].plot(time_tc, tc_horizontal, '-d', linewidth=1.5, markersize=2, label=tcver)
    axes1[0].set_title('Horizontal Error')
    # 只保留最后一行的x轴标签
    axes1[0].set_xlabel('')
    axes1[0].set_ylabel('Error (m)')

    # 设置坐标轴范围，确保所有曲线都能清晰显示
    all_horizontal_data = np.array([])
    if len(gnss_horizontal) > 0:
        all_horizontal_data = np.concatenate([all_horizontal_data, gnss_horizontal])
    if len(lc_horizontal) > 0:
        all_horizontal_data = np.concatenate([all_horizontal_data, lc_horizontal])
    if len(tc_horizontal) > 0:
        all_horizontal_data = np.concatenate([all_horizontal_data, tc_horizontal])
    if len(all_horizontal_data) > 0:
        y_range = np.max(all_horizontal_data) - np.min(all_horizontal_data)
        y_margin = y_range * 0.1  # 添加10%的边距
        axes1[0].set_ylim([np.min(all_horizontal_data) - y_margin, np.max(all_horizontal_data) + y_margin])

    # 只在第一个子图显示图例
    axes1[0].legend()

    # 绘制横向误差（第二行）
    axes1[1].grid(True)
    # 调整绘图顺序，如果画了gnss，就画在第一个
    if len(time_gnss) > 0 and len(gnss_lateral) > 0:
        axes1[1].plot(time_gnss, gnss_lateral, '-o', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_lc) > 0 and len(lc_lateral) > 0:
        axes1[1].plot(time_lc, lc_lateral, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_tc) > 0 and len(tc_lateral) > 0:
        axes1[1].plot(time_tc, tc_lateral, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
    axes1[1].set_title('Lateral Error')
    # 只保留最后一行的x轴标签
    axes1[1].set_xlabel('')
    axes1[1].set_ylabel('Error (m)')

    # 设置坐标轴范围，确保所有曲线都能清晰显示
    all_lateral_data = np.array([])
    if len(gnss_lateral) > 0:
        all_lateral_data = np.concatenate([all_lateral_data, gnss_lateral])
    if len(lc_lateral) > 0:
        all_lateral_data = np.concatenate([all_lateral_data, lc_lateral])
    if len(tc_lateral) > 0:
        all_lateral_data = np.concatenate([all_lateral_data, tc_lateral])
    if len(all_lateral_data) > 0:
        y_range = np.max(all_lateral_data) - np.min(all_lateral_data)
        y_margin = y_range * 0.1  # 添加10%的边距
        axes1[1].set_ylim([np.min(all_lateral_data) - y_margin, np.max(all_lateral_data) + y_margin])

    # 不显示图例
    axes1[1].legend().set_visible(False)

    # 绘制前进方向误差（第三行）
    axes1[2].grid(True)
    # 调整绘图顺序，如果画了gnss，就画在第一个
    if len(time_gnss) > 0 and len(gnss_forward) > 0:
        axes1[2].plot(time_gnss, gnss_forward, '-o', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_lc) > 0 and len(lc_forward) > 0:
        axes1[2].plot(time_lc, lc_forward, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_tc) > 0 and len(tc_forward) > 0:
        axes1[2].plot(time_tc, tc_forward, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
    axes1[2].set_title('Forward Error')
    # 只保留最后一行的x轴标签
    axes1[2].set_xlabel('')
    axes1[2].set_ylabel('Error (m)')

    # 设置坐标轴范围，确保所有曲线都能清晰显示
    all_forward_data = np.array([])
    if len(gnss_forward) > 0:
        all_forward_data = np.concatenate([all_forward_data, gnss_forward])
    if len(lc_forward) > 0:
        all_forward_data = np.concatenate([all_forward_data, lc_forward])
    if len(tc_forward) > 0:
        all_forward_data = np.concatenate([all_forward_data, tc_forward])
    if len(all_forward_data) > 0:
        y_range = np.max(all_forward_data) - np.min(all_forward_data)
        y_margin = y_range * 0.1  # 添加10%的边距
        axes1[2].set_ylim([np.min(all_forward_data) - y_margin, np.max(all_forward_data) + y_margin])

    # 不显示图例
    axes1[2].legend().set_visible(False)

    # 绘制垂直误差（第四行）
    axes1[3].grid(True)
    # 调整绘图顺序，如果画了gnss，就画在第一个
    if len(time_gnss) > 0 and len(gnss_vertical) > 0:
        axes1[3].plot(time_gnss, gnss_vertical, '-o', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_lc) > 0 and len(lc_vertical) > 0:
        axes1[3].plot(time_lc, lc_vertical, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
    if len(time_tc) > 0 and len(tc_vertical) > 0:
        axes1[3].plot(time_tc, tc_vertical, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
    axes1[3].set_title('Vertical Error')
    # 最后一行保留x轴标签
    axes1[3].set_xlabel('Time (s)')
    axes1[3].set_ylabel('Error (m)')

    # 设置坐标轴范围，确保所有曲线都能清晰显示
    all_vertical_data = np.array([])
    if len(gnss_vertical) > 0:
        all_vertical_data = np.concatenate([all_vertical_data, gnss_vertical])
    if len(lc_vertical) > 0:
        all_vertical_data = np.concatenate([all_vertical_data, lc_vertical])
    if len(tc_vertical) > 0:
        all_vertical_data = np.concatenate([all_vertical_data, tc_vertical])
    if len(all_vertical_data) > 0:
        y_range = np.max(all_vertical_data) - np.min(all_vertical_data)
        y_margin = y_range * 0.1  # 添加10%的边距
        axes1[3].set_ylim([np.min(all_vertical_data) - y_margin, np.max(all_vertical_data) + y_margin])

    # 不显示图例
    axes1[3].legend().set_visible(False)

    # 创建第二个图形窗口：不带GNSS（只有在不是只绘制GNSS时才创建）
    fig2 = None
    if not only_gnss:
        fig2, axes2 = plt.subplots(4, 1, figsize=(12, 16))
        fig2.suptitle('Error Analysis (Without GNSS)', fontsize=16)
        
        # 如果是详细子图模式，设置x轴刻度格式为显示完整数值
        if is_detail:
            for ax in axes2:
                ax.ticklabel_format(style='plain', axis='x', useOffset=False)

        # 绘制不带GNSS的水平误差（第一行）
        axes2[0].grid(True)
        if len(time_lc) > 0 and len(lc_horizontal) > 0:
            axes2[0].plot(time_lc, lc_horizontal, '-s', linewidth=1.5, markersize=2, label=lcver)
        if len(time_tc) > 0 and len(tc_horizontal) > 0:
            axes2[0].plot(time_tc, tc_horizontal, '-d', linewidth=1.5, markersize=2, label=tcver)
        axes2[0].set_title('Horizontal Error (Without GNSS)')
        # 只保留最后一行的x轴标签
        axes2[0].set_xlabel('')
        axes2[0].set_ylabel('Error (m)')

        # 设置坐标轴范围，确保所有曲线都能清晰显示
        all_horizontal_data_no_gnss = np.array([])
        if len(lc_horizontal) > 0:
            all_horizontal_data_no_gnss = np.concatenate([all_horizontal_data_no_gnss, lc_horizontal])
        if len(tc_horizontal) > 0:
            all_horizontal_data_no_gnss = np.concatenate([all_horizontal_data_no_gnss, tc_horizontal])
        if len(all_horizontal_data_no_gnss) > 0:
            y_range = np.max(all_horizontal_data_no_gnss) - np.min(all_horizontal_data_no_gnss)
            y_margin = y_range * 0.1  # 添加10%的边距
            axes2[0].set_ylim([np.min(all_horizontal_data_no_gnss) - y_margin, np.max(all_horizontal_data_no_gnss) + y_margin])

        # 只在第一个子图显示图例
        axes2[0].legend()

        # 绘制不带GNSS的横向误差（第二行）
        axes2[1].grid(True)
        if len(time_lc) > 0 and len(lc_lateral) > 0:
            axes2[1].plot(time_lc, lc_lateral, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
        if len(time_tc) > 0 and len(tc_lateral) > 0:
            axes2[1].plot(time_tc, tc_lateral, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
        axes2[1].set_title('Lateral Error (Without GNSS)')
        # 只保留最后一行的x轴标签
        axes2[1].set_xlabel('')
        axes2[1].set_ylabel('Error (m)')

        # 设置坐标轴范围，确保所有曲线都能清晰显示
        all_lateral_data_no_gnss = np.array([])
        if len(lc_lateral) > 0:
            all_lateral_data_no_gnss = np.concatenate([all_lateral_data_no_gnss, lc_lateral])
        if len(tc_lateral) > 0:
            all_lateral_data_no_gnss = np.concatenate([all_lateral_data_no_gnss, tc_lateral])
        if len(all_lateral_data_no_gnss) > 0:
            y_range = np.max(all_lateral_data_no_gnss) - np.min(all_lateral_data_no_gnss)
            y_margin = y_range * 0.1  # 添加10%的边距
            axes2[1].set_ylim([np.min(all_lateral_data_no_gnss) - y_margin, np.max(all_lateral_data_no_gnss) + y_margin])

        # 不显示图例
        axes2[1].legend().set_visible(False)

        # 绘制不带GNSS的前进方向误差（第三行）
        axes2[2].grid(True)
        if len(time_lc) > 0 and len(lc_forward) > 0:
            axes2[2].plot(time_lc, lc_forward, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
        if len(time_tc) > 0 and len(tc_forward) > 0:
            axes2[2].plot(time_tc, tc_forward, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
        axes2[2].set_title('Forward Error (Without GNSS)')
        # 只保留最后一行的x轴标签
        axes2[2].set_xlabel('')
        axes2[2].set_ylabel('Error (m)')

        # 设置坐标轴范围，确保所有曲线都能清晰显示
        all_forward_data_no_gnss = np.array([])
        if len(lc_forward) > 0:
            all_forward_data_no_gnss = np.concatenate([all_forward_data_no_gnss, lc_forward])
        if len(tc_forward) > 0:
            all_forward_data_no_gnss = np.concatenate([all_forward_data_no_gnss, tc_forward])
        if len(all_forward_data_no_gnss) > 0:
            y_range = np.max(all_forward_data_no_gnss) - np.min(all_forward_data_no_gnss)
            y_margin = y_range * 0.1  # 添加10%的边距
            axes2[2].set_ylim([np.min(all_forward_data_no_gnss) - y_margin, np.max(all_forward_data_no_gnss) + y_margin])

        # 不显示图例
        axes2[2].legend().set_visible(False)

        # 绘制不带GNSS的垂直误差（第四行）
        axes2[3].grid(True)
        if len(time_lc) > 0 and len(lc_vertical) > 0:
            axes2[3].plot(time_lc, lc_vertical, '-s', linewidth=1.5, markersize=2, label='_nolegend_')
        if len(time_tc) > 0 and len(tc_vertical) > 0:
            axes2[3].plot(time_tc, tc_vertical, '-d', linewidth=1.5, markersize=2, label='_nolegend_')
        axes2[3].set_title('Vertical Error (Without GNSS)')
        # 最后一行保留x轴标签
        axes2[3].set_xlabel('Time (s)')
        axes2[3].set_ylabel('Error (m)')

        # 设置坐标轴范围，确保所有曲线都能清晰显示
        all_vertical_data_no_gnss = np.array([])
        if len(lc_vertical) > 0:
            all_vertical_data_no_gnss = np.concatenate([all_vertical_data_no_gnss, lc_vertical])
        if len(tc_vertical) > 0:
            all_vertical_data_no_gnss = np.concatenate([all_vertical_data_no_gnss, tc_vertical])
        if len(all_vertical_data_no_gnss) > 0:
            y_range = np.max(all_vertical_data_no_gnss) - np.min(all_vertical_data_no_gnss)
            y_margin = y_range * 0.1  # 添加10%的边距
            axes2[3].set_ylim([np.min(all_vertical_data_no_gnss) - y_margin, np.max(all_vertical_data_no_gnss) + y_margin])

        # 不显示图例
        axes2[3].legend().set_visible(False)

    # 调整子图间距
    plt.tight_layout()

    # 保存图像为PNG格式
    if save_path and save_path.strip():  # 检查save_path是否非空
        # 确保保存路径包含.png后缀
        if not save_path.endswith('.png'):
            save_path_base = save_path
        else:
            # 如果已经有.png后缀，去掉它以便添加新的后缀
            save_path_base = save_path[:-4]

        # 保存带GNSS的图像
        fig1.savefig(f'{save_path_base}_with_gnss.png', dpi=300, bbox_inches='tight')
        
        # 只有在不是只绘制GNSS时才保存不带GNSS的图像
        if not only_gnss and fig2 is not None:
            fig2.savefig(f'{save_path_base}_without_gnss.png', dpi=300, bbox_inches='tight')

    # 关闭所有图形窗口，避免阻塞后续处理
    plt.close('all')

# 示例调用（如果直接运行此脚本）
if __name__ == "__main__":
    # 这里可以添加示例代码来测试函数
    pass