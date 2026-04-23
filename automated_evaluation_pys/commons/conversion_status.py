"""
MATLAB to Python 转换状态跟踪
"""

# 已完成转换的脚本
completed_scripts = [
    'getParentDirectory.py',
    'skipCommentLines.py',
    'calculate_cep.py',
    'calculate_errors.py',
    'readSensorData.py',
    'alignDataByTimeTcSol.py',
    'plot_errors.py',
    'compare_tc_gnsstopic.py',
    'calculateDifferenceTcSol.py',
    'plot_precision_comparison.py',
    'tr2rpy.py',
    'plot_skyview.py',
    'skyplot.py',
    'calculate_odometry.py',
    'readSensorDataTcSol.py',
    'calculateDifferenceTcSol_sp.py',
    'readSensorDataTcXkPk.py',
    'readmsf_debug_state.py',
    'readgnsstopic.py',
    'readgnsscsv.py',
    'plotgnsscsv.py',
    'compare_2msfstate.py',
    'plot_stats_comparison.py',
    'StatsComparisonAll.py',
    'plotStatsComparisonaAll.py',
    'compare_tc_lc.py',
    'compare_tc_lc_mul.py',
    'load100ccsv.py',
    'compare_tc_lc_ref_100c.py',
    'att_diff_adjust.py',
    'precision_tc_lc_ref_100c.py',
    'plot_precision_errors.py',
    'cmp2tcstats.py',
    'compareTCHisStatistics.py',
    'compareDH_Dalt.py',
    'blockAverage_loop.py',
    'bppaps.py',
    'bppaps_huiguan.py',
    'precision3d_tc_lc_ref_100c_.py',
    'compare_lc_gnsstopic.py',
    'read_rts_file.py',
    'precision3d_rts_ref_100c.py',
    'test_alignDataByTimeTcSol.py'
]

# 剩余需要转换的MATLAB脚本
remaining_scripts = [
    'compare_lc_gnsstopic.m',
    'compare_rtkpos_gnsstopic.m',
    'compare_tc2_gnsstopic.m',
    'compare_tc_gnsstopic_no_P.m',
    'compare_tc_lc_msfstate.m',
    'compare_tc_lc_ref_postpva.m',
    'compare_tc_lc_tcmsftopic.m',
    'detaH.m',
    'diff_2msfstate.m',
    'diff_tc_rt_post.m',
    'diff_tc_rt_post_3D.m',
    'diffeclaps.m',
    'diffimu.m',
    'dtcal.m',
    'dv.m',
    'extractDirDates.m',
    'filterAByBTime.m',
    'getdtinindexs.m',
    'gnsstime100ms.m',
    'load100c.m',
    'matchDateDirectories.m',
    'meanBasedTrendDetector.m',
    'outpre_new.m',
    'parseGGA2GPS.m',
    'plot_precision_comparison_four.m',
    'precision3d_tc_lc_ref_100c_gga_.m',
    'precision3d_tc_lc_ref_msftopic.m',
    'precision_head_topic_ref_100c_wdh.m',
    'precision_huiguan.m',
    'precision_msfdbg_ref_100c_wdh.m',
    'precision_tc_lc_ref_100c_pb_onepic.m',
    'precision_tcmsf_lctcmsf.m',
    'precision_tcmsf_lctcmsf_mul.m',
    'precision_topic_ref_100c_wdh.m',
    'processGGAFile.m',
    'processdtindex.m',
    'read_gnss_cnoa.m',
    'read_gps_data_wdh.m',
    'readgcj02_localization.m',
    'readmsf_debug_state_cnoa.m',
    'readmsftopic.m',
    'readpostpva.m',
    'readtcmsfcsv.m',
    'readtcmsftopic.m',
    'readtcmsftopic_ant_mars.m',
    'result_statistics.m',
    'slidingAvg.m',
    'slidingWindowAnomalyDetector.m',
    'subtractTimeRangesVectorized.m',
    'tcmsf_topic_cmpare.m',
    'tcmsfcsvdiff.m',
    'test.m',
    'test1.m',
    'test2.m',
    'test3.m',
    'test5.m',
    'test6.m',
    'test_sym.m',
    'trendChangeDetector.m',
    'trendChangeDetectorWithPlot.m',
    'veh_fb_pos_ana.m',
    'veh_fb_pos_ana_batch.m',
    'veh_fb_pos_ana_test1.m',
    'vehdpos.m',
    'windowedTrendChangeDetector.m'
]

def get_conversion_status():
    """
    获取转换状态
    """
    total_scripts = len(completed_scripts) + len(remaining_scripts)
    conversion_rate = round((len(completed_scripts) / total_scripts) * 100, 1)
    
    status = {
        'total_scripts': total_scripts,
        'converted_scripts': len(completed_scripts),
        'remaining_scripts': len(remaining_scripts),
        'conversion_rate': f'{conversion_rate}%',
        'status': 'In Progress',
        'completed_scripts': completed_scripts,
        'remaining_scripts': remaining_scripts
    }
    return status

if __name__ == "__main__":
    status = get_conversion_status()
    print(f"MATLAB to Python Conversion Status")
    print("="*40)
    print(f"Total Scripts: {status['total_scripts']}")
    print(f"Converted Scripts: {status['converted_scripts']}")
    print(f"Remaining Scripts: {status['remaining_scripts']}")
    print(f"Conversion Rate: {status['conversion_rate']}")
    print(f"Status: {status['status']}")
    
    print("\nCompleted Scripts:")
    for i, script in enumerate(status['completed_scripts'], 1):
        print(f"  {i:2d}. {script}")
    
    print("\nRemaining Scripts:")
    for i, script in enumerate(status['remaining_scripts'], 1):
        print(f"  {i:2d}. {script}")
