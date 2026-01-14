#!/usr/bin/python3
import time

class BenchTimeUsage():
    def __init__(self):
        pass

    @staticmethod
    def _print_time_usage(
        str_text: str="",
        flt_time_last : float=0.0,
        bol_time_benchmark : bool = True,
    ):
        """ 打印时间使用情况
        """
        if not bol_time_benchmark:
            return flt_time_last
        flt_time_current = time.time()
        flt_time_used = flt_time_current - flt_time_last
        print(str_text.format(flt_time_used))
        return flt_time_current
