"""
PVT RTK LC Evaluation Package Setup
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_file(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, filename), encoding='utf-8') as f:
        return f.read()

# 读取版本信息
version = {}
with open(os.path.join('pvt_rtk_lc_evaluation', '__init__.py')) as fp:
    exec(fp.read(), version)
    version = version.get('__version__', '1.0.0')

setup(
    name='pvt-rtk-lc-evaluation',
    version=version,
    description='PVT RTK LC精度评估工具包',
    long_description=read_file('README.md') if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    author='BYD ADAS Team',
    packages=find_packages(exclude=['tests*', 'docs*']),
    include_package_data=True,
    install_requires=[
        'numpy>=1.21.0',
        'pandas>=1.3.0',
        'matplotlib>=3.4.0',
        'scipy>=1.7.0',
        'toml>=0.10.2',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'precision-eval=pvt_rtk_lc_evaluation.precision_head_topic_ref_100c_wdh:main',
            'precision-eval-horizontal=pvt_rtk_lc_evaluation.precision_head_topic_ref_100c_wdh_horizontal_only:main',
            'batch-run-tcmsf=pvt_rtk_lc_evaluation.batch_run_tcmsf:main',
            'batch-run-precision=pvt_rtk_lc_evaluation.batch_run_precision_head_horizontal:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)