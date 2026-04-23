#!/bin/bash
#主要用于非依赖包变化的自编脚本的上传

cd /home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/record_evo/scripts/ossutil-v1.7.19-linux-amd64
configfile=config.txt
destosspath=oss://oss-byd-wl-roadtest/users/localization/split_data/programs/
#objfile=/home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/automated_evaluation_pys/pvt_rtk_lc_evaluation_deploy_python310.tar.gz
#objfile=/home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/automated_evaluation_pys/pvt_rtk_lc_evaluation_deploy.tar.gz

tarfile=/home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/automated_evaluation_pys/pvt_rtk_lc_evaluation.tar
rm ${tarfile}
tar -czvf ${tarfile} -C /home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/automated_evaluation_pys pvt_rtk_lc_evaluation commons
#tarfile=/home/wufengbo/workcode/repos/cnoa/byd_adas_app/modules/util/automated_evaluation_pys/pvt_rtk_lc_evaluation/precision_head_topic_ref_100c_wdh_horizontal_only.py
./ossutil cp --jobs=16 --config-file=${configfile} ${tarfile} ${destosspath} --recursive
