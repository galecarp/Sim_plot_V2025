#!/usr/bin/env python3

from typing import List, Dict, Optional, Union, Any, Callable, Iterable, TYPE_CHECKING, override
from functools import partial, reduce
from itertools import starmap

@staticmethod
def aggregate_info_iterable(
    iter_tgt: Iterable,
    extractors: Union[str, List[str], Callable] = None,
    filter_pre: Optional[Callable] = None,
    filter_post: Optional[Callable] = None,
    aggregator: Optional[Callable] = None
) -> Any:
    """
    聚合所有Iterable的信息
    """
    # 默认值处理
    if extractors is None:
        extractors = lambda mgr: mgr
    # 标准化 extractors 为 callable
    if isinstance(extractors, str):
        # 单个方法名 → 转为函数
        method_name = extractors
        extractors = [
            lambda mgr: getattr(mgr, method_name)()
        ] * len(iter_tgt)
    elif isinstance(extractors, Callable):
        extractors = [extractors] * len(iter_tgt)
    elif isinstance(extractors, Iterable):
        # 检验长度:
        if len(extractors) != len(iter_tgt):
            raise ValueError("extractors列表长度必须与subplot数量一致")
        # 转化为函数列表
        extractors = [
            lambda mgr, method_name=method_name: getattr(mgr, method_name)()
            for method_name in extractors
            if isinstance(method_name, str)
        ]
    else:
        raise TypeError("extractors参数类型不支持")

    res = iter_tgt
    # 1.过滤Pre
    if filter_pre is not None:
        res = filter(filter_pre, res)
    # 2.提取数据
    func_extract = lambda idx, obj: extractors[idx](obj)
    res = starmap(
        func_extract,
        enumerate(iter_tgt))
    
    # 3.过滤Post
    if filter_post is not None:
        res = filter(filter_post, res)
    # 4.聚合
    if aggregator is not None:
        res = reduce(aggregator, res)
    else:
        res = list(res)
    return res

@staticmethod
def aggregator_list(
    x: Union[List[Any], Any],
    y: Any
) -> List[Any]:
    """
    将元素添加到列表中，作为聚合器使用
    """
    if isinstance(x, list):
        return x + [y]
    else:
        return [x, y]
