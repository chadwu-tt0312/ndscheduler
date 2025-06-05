import sys
import datetime
import argparse

# 設定命令列參數解析
parser = argparse.ArgumentParser(description="測試 Python Job 的參數傳遞")
parser.add_argument("--arg1", type=str, default="default_value1", help="第一個參數")
parser.add_argument("--arg2", type=str, default="default_value2", help="第二個參數")

# 解析參數
args = parser.parse_args()

print(f"Received arg1: {args.arg1}")
print(f"Received arg2: {args.arg2}")
print(f"All command line arguments: {sys.argv}")

print(f"Python version: {sys.version}")
print(f"Current time: {datetime.datetime.now()}")
print("Test script executed successfully!")
