from typing import Callable, Optional

func = list[Callable]

class ParserChain:
    def __init__(self, funcs: Optional[func] = None):
        self.funcs: func = [] if funcs is None else funcs

    def add(self, func:func):
        '''添加一个函数 / 装饰器'''
        self.funcs.append(func)
        return func

    def remove(self, func:func):
        '''删除一个函数'''
        self.funcs.remove(func)

    @property
    def get_funcs(self):
        return self.funcs

    def run(self, *args, **kwargs):
        '''按照列表的反向顺序执行'''
        for func in reversed(self.funcs):
            result = func(*args, **kwargs)

            if result is not None:
                return result

def test_main():
    # ---------------- 示例 ----------------
    chain = ParserChain()

    @chain.add
    def low(v):                       # 最先添加 → 最后执行
        return f"low({v})"

    @chain.add
    def mid(v):                       # 第二个添加
        return None if v < 10 else f"mid({v})"

    @chain.add
    def high(v):                      # 最后添加 → 最先执行
        return None if v < 100 else f"high({v})"

    @chain.add
    def no_add(v):
        raise ValueError('This is Added and runed!')

    chain.remove(no_add)

    assert chain.get_funcs == [low, mid, high]
    assert chain.run(5) == "low(5)"    # high→None, mid→None, low→"low(5)"
    assert chain.run(50) == "mid(50)"    # high→None, mid→"mid(50)"
    assert chain.run(500) == "high(500)"   # "high(500)"

    # 用列表初始化也支持
    c2 = ParserChain([lambda v: None, lambda v: f"got {v}"])
    assert c2.run(1) == "got 1"        # "got 1"
    assert ParserChain().run(1) is None  # None