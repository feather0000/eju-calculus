# 验算 快速解题技巧 中的例题数值
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from math_tips import TIPS
from _x import tip_check
print(f'{len(TIPS)} tips, {tip_check(TIPS)} worked-example numeric checks, 0 failures')
