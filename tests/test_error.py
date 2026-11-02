from typing import Optional, Callable

func = list[Callable]

class ParserChain:
    def __init__(self, funcs: Optional[func] = None):
        self._funcs = [] if funcs is None else funcs

        if funcs is not None:
            self.funcs = funcs # 初始校验

    def add(self, func:func):
        '''添加一个函数 / 装饰器'''
        self.funcs.append(func)
        self.check(func)
        return func

    def remove(self, func:func):
        '''删除一个函数'''
        self.funcs.remove(func)

    def set(self, funcs: func):
        self.funcs = funcs

    @property
    def funcs(self):
        return self._funcs

    @funcs.setter
    def funcs(self, v):
        self.check(v)

    def check(self, v):
        if isinstance(v, list):
            for func in v:
                if not isinstance(func, Callable):
                    raise TypeError('Function list item must be function')
            self._funcs = v
        else:
            raise TypeError('Function list must be list')

    def run(self, *args, **kwargs):
        '''按照列表的反向顺序执行'''
        for func in reversed(self.funcs):
            result = func(*args, **kwargs)

            if result is not None:
                return result

def test_main():
    try:
        ParserChain(123) # 初始化：不是列表

        assert False
    except TypeError:
        print('Success!')

    try:
        ParserChain([123]) # 初始化：列表项不是函数

        assert False
    except TypeError:
        print('Success!')

    try:
        v = ParserChain([]) # 初始化：列表项不是函数
        v.set(123) # 设置非法值

        assert False
    except TypeError:
        print('Success!')

    try:
        v = ParserChain([]) # 初始化：列表项不是函数
        v.add(123) # 添加非法值

        assert False
    except TypeError:
        print('Success!')

    try:
        v = ParserChain([]) # 初始化：列表项不是函数
        v.funcs = 123 # 连接非法值

        assert False
    except TypeError:
        print('Success!')