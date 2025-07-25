########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    log_error,
    sleep,
    read_file,
    write_file,
    format_json,
    loop_dir,
    excel_to_df,
)

########################################

import argparse
import os
import time
import traceback
from datetime import datetime
import pandas as pd

############### SAMPLE ################
# time.sleep(1)


def traverse_fifth_sheet(file_path):
    # 读取Excel文件
    xls = pd.ExcelFile(file_path)
    # 获取所有sheet名称
    sheet_names = xls.sheet_names
    if len(sheet_names) < 5:
        log_error("Excel文件中少于5个sheet")
        return
    # 读取第5个sheet（索引从0开始）
    df = pd.read_excel(xls, sheet_name=sheet_names[4])
    log(f"遍历第5个sheet: {sheet_names[4]}")
    for idx, row in df.iterrows():
        log(f"第{idx+1}行: {row.to_dict()}")
        # 遍历第四个sheet的J列（假设J列为第10列，索引为9），如果包含当前行第一个值，则打印第四个sheet的J列值
        df4 = pd.read_excel(xls, sheet_name=sheet_names[3])
        first_value = row.iloc[0]
        if df4.shape[1] >= 10:  # 确保有J列
            j_col = df4.iloc[:, 9]
            if j_col.astype(str).str.contains(str(first_value._date_repr)).any():
                log(f"第4个sheet的J列值: {j_col.tolist()}")


def filter_and_save(file_path, sheet_name=None):
    # 读取Excel文件
    xls = pd.ExcelFile(file_path)
    sheet_names = xls.sheet_names
    if len(sheet_names) < 5:
        log_error("Excel文件中少于5个sheet")
        return
    # 读取第5个sheet
    df = pd.read_excel(xls, sheet_name=sheet_names[4])
    log(f"第5个sheet数据：\n{df}")


########################################
def build_arg_parser():
    parser = argparse.ArgumentParser(description="Action")
    parser.add_argument("--action", dest="action", required=False, help="action")
    parser.add_argument("--text", dest="text", required=False, help="text")
    args, left = parser.parse_known_args()
    return args


def test(txt):
    log(txt)


########################################
# BODY #
########################################
"""
INPUT YOUR SCRIPT HERE
"""
########################################
########################################

# BOTTOM #
########################################
if __name__ == "__main__":
    try:
        start = datetime.now()
        args = build_arg_parser()
        log(f"__dir__: {__file__}")
        log(f"### [start-try]: action=[{args.action}]")
        ###########################################
        if args.action == "test":
            test(args.text)
        else:
            traverse_fifth_sheet(
                file_path="D:\__Lemmy\十四中附属学校\学习总结.xlsx"
            )  ###########################################
        end = datetime.now()
        inter = end - start
        log(f"### [end-try]: [{inter}]")
    except:
        traceback.print_exc()
    finally:
        fine = datetime.now()
        inter = fine - start
        log(f"### [finally]: [{inter}]")
