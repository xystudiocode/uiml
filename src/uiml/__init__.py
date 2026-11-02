from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Callable
from deprecated import deprecated
from warnings import warn

try:
    from uiml.uilib import *
except ImportError as e:
    if "libEGL.so.1" in str(e):
        pass
    else:
        raise

import inspect
import re
from contextvars import ContextVar
from enum import Enum

__version__ = '0.3.0a1'
_UNICODE = re.compile(r'&#[xX]([0-9a-fA-F]+);',)
func = list[Callable]

namespace_api_enabled = False

class ParserEnum(Enum):
    replacer = 1 # 参数替换器
    widget_parser = 2 # 组件解析器
    layout_parser = 3 # 布局解析器
    namespace_parser = 4 # 命名空间的解析器

    uiml_class = 7 # 对layout渲染的扩展（注册自定义 UIMLLayout 渲染类）

class UsedKeyEnum(Enum):
    widget = 1 # 自动删除的组件项目列表
    layout = 2 # 自动删除的布局项目列表

class ParamEnum(Enum):
    reverse_namespace = 1 # 翻转命名空间顺序
    value_convert = 2 # 允许变量转化
    debug_mode = 3 # 调试模式

class ControlEnum(Enum):
    reset = 1 # 重置组件

class _NoPaint:
    '''特殊值类型：表示该节点已处理，但不需要绘制到窗口上。'''
    __slots__ = ()

    def __repr__(self):
        return 'NoPaint'

# 特殊值：解析器返回 NoPaint 时会停止解析链，并且该节点不会被绘制。
# 与 None 不同，None 表示继续执行下一个解析器。
NoPaint = _NoPaint()

class ParserChain:
    def __init__(self, funcs: Optional[func] = None):
        self._funcs = [] if funcs is None else funcs
        self._default_funcs = [] # 默认函数列表

        if funcs is not None:
            self.funcs = funcs # 初始校验

        if namespace_api_enabled:
            raise UIMLException('Namespace API is enabled, please disable it first. ')

    def add(self, func:func):
        '''添加一个函数 / 装饰器'''
        self.funcs.append(func)
        self.check(self.funcs)
        return func

    def add_default(self, func: func):
        '''添加一个默认函数 / 装饰器'''
        self.add(func)

        self._default_funcs.append(func)
        self._validate(self._default_funcs)

        return func

    def reset(self):
        self.set(self._default_funcs.copy())

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
        self._validate(v)
        self._funcs = v

    @staticmethod
    def _validate(v):
        if isinstance(v, list):
            for func in v:
                if not isinstance(func, Callable):
                    raise TypeError('Function list item must be function')
        else:
            raise TypeError('Function list must be list')

    def run(self, *args, **kwargs):
        '''按照列表的反向顺序执行'''
        for func in reversed(self.funcs):
            result = func(*args, **kwargs)

            if result is not None:
                return result

replacer_chain = ParserChain()
widget_parser_chain = ParserChain()
layout_parser_chain = ParserChain()
namespace_parser_chain = ParserChain()
uiml_class_chain = ParserChain()

# 防止解析器内部再次构造 UIMLLayout 时无限递归
_uiml_class_resolving = ContextVar('uiml_class_resolving', default=False)

default_used_widget_key = ['name', 'type', 'args', 'kwargs', 'init_steps', 'signals', 'style']
default_used_layout_key = ['name', 'direction', 'content', 'stretch']

default_config = {'reverse_namespace': False, 'value_convert': True, 'debug_mode': False}
config = default_config.copy()  # 默认配置

used_widget_key = default_used_widget_key.copy()
used_layout_key = default_used_layout_key.copy()

def add_parser(enum: ParserEnum, value: Callable | ControlEnum):
    match enum:
        case ParserEnum.replacer:
            chain = replacer_chain
        case ParserEnum.widget_parser:
            chain = widget_parser_chain
        case ParserEnum.layout_parser:
            chain = layout_parser_chain
        case ParserEnum.namespace_parser:
            chain = namespace_parser_chain
        case ParserEnum.uiml_class:
            chain = uiml_class_chain
        case _:
            raise ValueError(f'Unknown parser enum: {enum.name}')

    if value == ControlEnum.reset:
        chain.reset()
    else:
        chain.add(value)

def add_used_key(enum: UsedKeyEnum, value: list[str] | ControlEnum):
    match enum:
        case UsedKeyEnum.widget:
            lst = used_widget_key
            default = default_used_widget_key
        case UsedKeyEnum.layout:
            lst = used_layout_key
            default = default_used_layout_key
        case _:
            raise ValueError(f'Unknown used key enum: {enum.name}')

    if value == ControlEnum.reset:
        lst[:] = default.copy()
    else:
        lst.extend(value)

def set_config(enum: ParamEnum, value: bool | ControlEnum):
    if value == ControlEnum.reset:
        config[enum.name] = default_config[enum.name]
        return
    config[enum.name] = value

skip_level=1

# 标签名/属性名中允许出现的符号（字母、数字、下划线之外）
# 例如模块路径 QtWidgets.QLabel 中的 '.'、XML 命名空间中的 ':'、kebab-case 中的 '-'
NAME_SYMBOLS = frozenset('._-:')

def is_name_char(ch: str) -> bool:
    '''判断字符是否可以出现在标签名或属性名中。'''
    return ch.isalnum() or ch in NAME_SYMBOLS

def load_namespace(check_global:bool=True, check_local: bool = False, reverse: bool=None, additional=None) -> Dict[str, Any]:
    '''
    获取当前调用方的命名空间（全局+局部变量合并）。

    参数:
        check_global: 是否检查全局命名空间。
        check_local: 是否检查局部命名空间。
    '''
    reverse = config['reverse_namespace'] if reverse is None else False
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if not config['value_convert']:
        return globals()
    
    stack = inspect.stack()
    if reverse:
        stack = reversed(stack)
    else:
        stack = stack
    # 从索引 1 开始（跳过当前帧 get_caller_namespace 自身）
    namespace = {}
    for frame_info in stack:
        frame = frame_info.frame
        if check_global:namespace.update(frame.f_globals)
        if (check_local and not(config['debug_mode'])):namespace.update(frame.f_locals)
    namespace.update(additional_value)  # 添加额外的值
    return namespace

def _run_namespace_parser():
    '''
    获取解析时使用的命名空间。

    - 旧版 Namespace API：使用 set_namespace 设置的 namespace_parser，保持原行为。
    - 新版 Parser API：运行 namespace_parser_chain，默认回退到 load_namespace。
    '''
    if namespace_api_enabled:
        return namespace_parser()
    return namespace_parser_chain.run()

def xml_parse(xml_str: str, namespace: Optional[Dict[str, Any]] = None, additional=None) -> Dict[str, Any]:
    '''
    将扩展 XML 字符串转换为 Python 字典。

    参数:
        xml_str: XML 字符串，支持属性值不带引号、Python 字面量（列表、字典、集合）、
                 变量/函数引用、表达式以及 true/false/null 字面量（任意嵌套）。
        namespace: 解析函数/变量时使用的命名空间（默认为调用方的全局+局部变量合并）。

    返回:
        解析后的字典，包含 'name' 键（标签名）、'content' 键（子元素或文本）以及所有属性。
    '''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    # 获取当前调用方的命名空间（全局+局部变量合并）
    if namespace is None:namespace = load_namespace(True, True, additional=additional_value)

    idx = 0
    n = len(xml_str)

    def skip_whitespace():
        nonlocal idx
        while idx < n and xml_str[idx].isspace():
            idx += 1

    def peek_char() -> str:
        return xml_str[idx] if idx < n else ''

    def parse_comment():
        nonlocal idx
        if xml_str.startswith('<!--', idx):
            idx += 4
            end = xml_str.find('-->', idx)
            if end == -1:
                raise ValueError("未找到注释结束标记 '-->'")
            idx = end + 3
            return None
        return False

    def parse_text() -> str:
        nonlocal idx
        start = idx
        while idx < n and xml_str[idx] != '<':
            idx += 1
        return xml_str[start:idx]

    def parse_tag_name_with_lt() -> str:
        nonlocal idx
        if xml_str[idx] != '<':
            raise ValueError(f"期望 '<'，实际 '{xml_str[idx]}'")
        idx += 1
        start = idx
        while idx < n and is_name_char(xml_str[idx]):
            idx += 1
        if start == idx:
            raise ValueError('无效的标签名')
        return xml_str[start:idx]

    def parse_tag_name_only() -> str:
        nonlocal idx
        start = idx
        while idx < n and is_name_char(xml_str[idx]):
            idx += 1
        if start == idx:
            raise ValueError('无效的标签名')
        return xml_str[start:idx]

    def preprocess_expr(expr: str) -> str:
        # 将表达式中的独立 true/false/null 替换为 Python 字面量
        expr = re.sub(r'\btrue\b', 'True', expr)
        expr = re.sub(r'\bfalse\b', 'False', expr)
        expr = re.sub(r'\bnull\b', 'None', expr)
        return expr

    def is_attribute_start(pos: int) -> bool:
        '''判断 pos 处是否是一个新属性的开头（形如 name=），用于区分裸值中的空格。'''
        k = pos
        while k < n and is_name_char(xml_str[k]):
            k += 1
        if k == pos:
            return False
        while k < n and xml_str[k].isspace():
            k += 1
        if k >= n or xml_str[k] != '=':
            return False
        # '==' 是比较运算符，不是属性赋值
        return k + 1 >= n or xml_str[k + 1] != '='

    def should_end_value_at(pos: int) -> bool:
        '''判断 pos 处的空白是否表示当前裸值结束（后面是下一个属性或标签结束）。'''
        k = pos
        while k < n and xml_str[k].isspace():
            k += 1
        if k >= n:
            return True
        if xml_str[k] == '>' or (xml_str[k] == '/' and k + 1 < n and xml_str[k + 1] == '>'):
            return True
        return is_attribute_start(k)

    def parse_attribute_value() -> Any:
        nonlocal idx
        if idx >= n:
            raise ValueError('属性值意外结束')

        ch = xml_str[idx]
        if ch in ('"', "'"):
            quote = ch
            idx += 1
            start = idx
            while idx < n and xml_str[idx] != quote:
                if xml_str[idx] == '\\' and idx + 1 < n:
                    idx += 2
                else:
                    idx += 1
            if idx >= n or xml_str[idx] != quote:
                raise ValueError(f'未找到匹配的引号 {quote}')
            value_str = xml_str[start:idx]
            idx += 1
            return value_str

        start = idx
        depth = 0
        quote = ''  # 当前所在的字符串字面量引号，'' 表示不在字符串中（支持 ''' 和 """）
        while idx < n:
            c = xml_str[idx]

            if quote:
                # 字符串内部：空白、'>'、'/>' 等都属于字符串内容
                if c == '\\' and idx + 1 < n:
                    idx += 2
                    continue
                if xml_str.startswith(quote, idx):
                    idx += len(quote)
                    quote = ''
                    continue
                idx += 1
                continue

            if c in ('"', "'"):
                if xml_str.startswith(c * 3, idx):
                    quote = c * 3
                    idx += 3
                else:
                    quote = c
                    idx += 1
                continue

            if c in '([{':
                depth += 1
            elif c in ')]}':
                if depth > 0:
                    depth -= 1
            elif depth == 0:
                if c.isspace():
                    # 裸值中可以包含空格（如 lambda:print('Clicked by layout!')），
                    # 只有空白后是下一个属性或标签结束时才结束当前值
                    if should_end_value_at(idx):
                        break
                elif c == '>' or (c == '/' and idx + 1 < n and xml_str[idx + 1] == '>'):
                    break
            idx += 1
        expr = xml_str[start:idx].strip()
        if not expr:
            raise ValueError('空的属性值')

        expr_processed = preprocess_expr(expr)

        try:
            return eval(expr_processed, namespace|additional_value)
        except NameError as e:
            raise NameError(f"未定义的标识符 '{expr}'，请检查命名空间或拼写：{e}")
        except Exception as e:
            raise ValueError(f"无法解析属性值 '{expr}': {e}")

    def parse_attributes() -> Dict[str, Any]:
        nonlocal idx
        attrs = {}
        while idx < n and xml_str[idx] != '>' and not (xml_str[idx] == '/' and idx + 1 < n and xml_str[idx + 1] == '>'):
            skip_whitespace()
            if xml_str[idx] == '>' or (xml_str[idx] == '/' and idx + 1 < n and xml_str[idx + 1] == '>'):
                break

            start = idx
            while idx < n and is_name_char(xml_str[idx]):
                idx += 1
            if start == idx:
                raise ValueError('无效的属性名')
            attr_name = xml_str[start:idx]

            skip_whitespace()
            if xml_str[idx] != '=':
                raise ValueError(f"属性 '{attr_name}' 后缺少 '='")
            idx += 1

            skip_whitespace()
            attr_value = parse_attribute_value()
            attrs[attr_name] = attr_value

        return attrs

    def parse_element() -> Dict[str, Any]:
        nonlocal idx

        while True:
            skip_whitespace()
            if xml_str.startswith('<!--', idx):
                if parse_comment() is None:
                    continue
            break

        if peek_char() != '<':
            text = parse_text()
            if text.strip():
                return {"content": text.strip()}
            return {}

        tag_name = parse_tag_name_with_lt()
        skip_whitespace()
        attrs = parse_attributes()

        if xml_str[idx] == '/' and idx + 1 < n and xml_str[idx + 1] == '>':
            idx += 2
            return {"type": tag_name, **attrs}

        if xml_str[idx] != '>':
            raise ValueError(f"期望 '>'，实际 '{xml_str[idx]}'")
        idx += 1

        children = []
        text_content = None

        while idx < n:
            skip_whitespace()
            if idx >= n:
                break

            if xml_str.startswith('<!--', idx):
                parse_comment()
                continue

            if xml_str.startswith('</', idx):
                idx += 2
                end_tag_name = parse_tag_name_only()
                skip_whitespace()
                if xml_str[idx] != '>':
                    raise ValueError(f"期望 '>'，实际 '{xml_str[idx]}'")
                idx += 1
                if end_tag_name != tag_name:
                    raise ValueError(f"结束标签不匹配: 期望 '{tag_name}'，实际 '{end_tag_name}'")
                break

            if xml_str[idx] == '<':
                child = parse_element()
                if child:
                    children.append(child)
                continue

            text = parse_text()
            if text:
                if children:
                    pass
                else:
                    text_content = text.strip()

        result = {"type": tag_name, **attrs}
        if text_content is not None:
            result["content"] = text_content
        elif children:
            result["content"] = children
        return result

    skip_whitespace()
    root = parse_element()
    return root

def xml_parse_file(file_path: str, namespace: Optional[Dict[str, Any]] = None, additional=None) -> Dict[str, Any]:
    '''
    从文件中读取扩展 XML 字符串并解析为 Python 字典。

    参数:
        file_path: 文件路径，支持属性值不带引号、Python 字面量（列表、字典、集合）、
                变量/函数引用、表达式等。
        namespace: 解析函数/变量时使用的命名空间（默认为调用方的全局命名空间）。
    '''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    with open(file_path, 'r', encoding='utf-8') as file:
        xml_str = file.read()  # 读取文件内容
    return xml_parse(xml_str, namespace, additional=additional_value)  # 解析 XML 字符串

def set_style(widget, class_name: str):
    '''
    设置按钮的class属性并刷新样式
    '''
    # 1. 设置class属性
    widget.setProperty('class', class_name)

    # 2. 强制样式刷新
    widget.style().unpolish(widget)
    widget.style().polish(widget)

    # 3. 触发重绘
    widget.update()

def enable_namespace_api():
    global namespace_api_enabled

    namespace_api_enabled = True

    set_namespace(
        default_replacer, default_layout_parser, default_widget_parser, 
        namespace_parser_func=load_namespace, reverse=False, 
        enable_value_convert=True, is_debug=False
    ) # 设置默认解析函数

    warn(
        'Namespace API is deprecated, please use Parser API (add_parser) instead. Now Parser API is disabled.',
         category=DeprecationWarning
    )

@deprecated(reason="Namespace API is deprecated, please use Parser API (add_parser) instead.")
def set_namespace(value_replace_func=None, layout_parser_func=None, widget_parser_func=None, 
                  additional_used_widget_key=None, additional_used_layout_key=None,
                  namespace_parser_func=None, reverse=None, enable_value_convert=None,
                  is_debug=None
                ):
    '''
    设置解析函数/变量时使用的操作。
    '''
    assert namespace_api_enabled, "Please add 'uiml.enable_namespace_api()' at the beginning of the code to enable the Namespace API"

    global replacer, layout_parser, widget_parser, used_widget_key, used_layout_key, namespace_parser
    if value_replace_func is not None:replacer = value_replace_func
    if layout_parser_func is not None:layout_parser = layout_parser_func
    if widget_parser_func is not None:widget_parser = widget_parser_func
    if additional_used_widget_key is not None:used_widget_key.extend(additional_used_widget_key)
    if additional_used_layout_key is not None:used_widget_key.extend(additional_used_layout_key) # 设置需要解析的字段
    if namespace_parser_func is not None:namespace_parser = namespace_parser_func
    if reverse is not None:config['reverse_namespace'] = reverse
    if enable_value_convert is not None:config['value_convert'] = enable_value_convert
    if is_debug is not None:config['debug_mode'] = is_debug

@replacer_chain.add_default
def default_replacer(value: str):
    '''默认替换函数，返回原值，可以自定义添加函数，如替换变量、函数调用等。'''
    unicode = re.sub(
        _UNICODE,
        lambda m: chr(int(m.group(1), 16)),
        value
    )
    return unicode

@namespace_parser_chain.add_default
def default_namespace_parser(*args, **kwargs):
    '''默认命名空间解析函数，使用 load_namespace 获取调用方命名空间。'''
    return load_namespace(*args, **kwargs)

@layout_parser_chain.add_default
def default_layout_parser(ui_data: Dict[str, Any], namespace: Dict[str, Any]=None, additional=None):
    '''默认布局解析函数，进行递归解析返回'''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if ui_data is NoPaint: return NoPaint
    if namespace is None:namespace = _run_namespace_parser() # 获取命名空间
    if ui_data is None: return {}
    
    other_values = _pop_dict(ui_data.copy(), used_layout_key)
    
    compiled_list = []
    for item in ui_data.get('content', []):
        ui = compile_ui(item, namespace, additional=additional_value) # 递归解析
        if ui is None or ui is NoPaint:continue
        compiled_list.append(ui) # 递归解析
    return {'name': ui_data.get('name'), 'direction': ui_data.get('direction'), 'content': compiled_list, 'stretch': ui_data.get('stretch', False), **other_values}

def reg_replacer(value):
    if isinstance(value, str):
        if namespace_api_enabled:
            return replacer(value) # 使用 Namespace API
        else:
            return replacer_chain.run(value) # 使用 Parser API
    elif isinstance(value, dict):
        return default_reg_replacer_dict(value)
    elif isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        return default_reg_replacer_list(value)
    else:
        return value

def default_reg_replacer_list(value):
    ls = []
    for i in value:
        ls.append(reg_replacer(i))
    return ls
            
def default_reg_replacer_dict(value):
    ls = {}
    for k, v in value.items():
        ls[k] = reg_replacer(v)
    return ls

def _pop_dict(dict_data, key):
    dict_copy = dict_data.copy()
    for k in key:
        dict_copy.pop(k, None)
    return dict_copy

@widget_parser_chain.add_default
def default_widget_parser(widget_data: Dict[str, Any], namespace: Dict[str, Any]=None, additional=None):
    '''默认控件解析函数，进行解析返回'''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if widget_data is NoPaint: return NoPaint
    if namespace is None:namespace = _run_namespace_parser() # 获取命名空间
 
    argv = [] # 参数
    kwargv = {} # 关键字参数
    style = widget_data.get('style', '') # 样式
    
    for arg in widget_data.get('args', []):
        argv.append(reg_replacer(arg))
            
    for k, arg in widget_data.get('kwargs', {}).items():
        kwargv[k] = reg_replacer(arg)
                
    widget = eval(f"{widget_data.get('type')}(*{argv}, **{kwargv})", namespace|additional_value)
    set_style(widget, style) # 设置样式

    for func in widget_data.get('init_steps', []):
        name = func['name']
        args = func.get('args', [])
        
        args_new =[]
        kwargs_new = {}
        
        for arg in args:
            args_new.append(reg_replacer(arg))
        kwargs = func.get('kwargs', {})
        
        for k, v in kwargs.items():
            kwargs_new[k] = reg_replacer(v)
        
        getattr(widget, name)(*args_new, **kwargs_new) # 执行初始化步骤
        
    for sign, func in widget_data.get('signals', {}).items():
        getattr(widget, sign).connect(func) # 连接信号
        
    other_values = _pop_dict(widget_data.copy(), used_widget_key)
    
    return {'name': widget_data.get('name'), 'content': widget, **other_values}

@uiml_class_chain.add_default
def default_uiml_class_parser(*args, **kwargs):
    '''默认 UI 类解析函数：返回 None，表示使用 UIMLLayout 自身进行渲染。'''
    return None

def compile_ui(ui_data, namespace=None, additional=None):
    if ui_data is NoPaint: # 该节点不绘制，也不再继续解析
        return NoPaint

    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if namespace is None:
        namespace = _run_namespace_parser() # 获取命名空间

    if ui_data.get('direction'): # 这是layout类型
        if namespace_api_enabled: # namespace API 语法
            return layout_parser(ui_data, namespace, additional=additional_value)
        else:
            return layout_parser_chain.run(ui_data, namespace, additional=additional)
    else: # 这是widget类型
        if namespace_api_enabled: # namespace API 语法
            return widget_parser(ui_data, namespace, additional=additional_value)
        else:
            return widget_parser_chain.run(ui_data, namespace, additional=additional)
    
def compile_ui_file(file_path: str, namespace=None, additional=None):
    '''
    从文件中读取扩展 XML 字符串并解析为 Python 字典，然后编译为布局或控件对象。

    参数:
        file_path: 文件路径，支持属性值不带引号、Python 字面量（列表、字典、集合）、变量/函数引用、表达式等。
        namespace: 解析函数/变量时使用的命名空间（默认为调用方的全局命名空间）。
    '''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    return compile_ui(xml_parse_file(file_path, namespace, additional=additional_value), namespace, additional=additional_value)  # 解析 XML 字符串并编译

namespace_parser = load_namespace

class _UIMLLayoutMeta(type):
    '''
    UIMLLayout 的元类，用于支持 Parser API（ParserEnum.uiml_class）。

    当直接构造 UIMLLayout 时，先运行 uiml_class_chain。如果解析器返回一个
    UIMLLayout 实例（通常是注册的自定义 UIMLLayout 子类），则直接使用该实例；
    返回 NoPaint 时不绘制；返回 None 时继续使用 UIMLLayout 自身。
    '''

    def __call__(cls, *args, **kwargs):
        if cls is UIMLLayout and not _uiml_class_resolving.get():
            token = _uiml_class_resolving.set(True) # 防止解析器内部再次构造 UIMLLayout 时无限递归
            try:
                parsed = uiml_class_chain.run(*args, **kwargs)
            finally:
                _uiml_class_resolving.reset(token)

            if parsed is NoPaint:
                return NoPaint
            if parsed is not None:
                if not isinstance(parsed, UIMLLayout):
                    raise TypeError(
                        'uiml_class parser must return a UIMLLayout instance, NoPaint or None, '
                        f'got {type(parsed).__name__}'
                    )
                return parsed

        return super().__call__(*args, **kwargs)

class UIMLLayout(metaclass=_UIMLLayoutMeta):
    '''布局渲染器；可通过 add_parser(ParserEnum.uiml_class, ...) 注册自定义渲染类。'''

    def __init__(self, list):
        self.list = list
        
    def find_widget(self, path: str, data=None):
        '''
        在嵌套字典结构中按点分隔路径查找元素。

        规则：
        - 路径中的每一段对应字典中的 'name' 字段。
        - 若当前节点是布局（含有 'direction' 键），且不是最后一段，则自动进入其子元素继续查找。
        - 布局的子元素在 'content' 列表中。
        - 最后一段如果是普通布局，返回其 'content' 列表；如果是 'u' 布局，返回 {'texts':..., 'inputs':..., 'combos':...}；如果是控件，返回其 'content'。
        - 如果根数据是 NoPaint，直接返回 NoPaint。
        - 路径必须完整且精确，找不到时抛出 KeyError。

        参数:
            path: 点分隔的路径字符串，如 "layout.vlayout.checkbox2"
            data: 根字典（例如 {'name': 'layout', 'direction': 'h', 'content': [...]}）

        返回:
            根据路径找到的控件对象、布局的 content 列表，或 'u' 布局的 texts/inputs/combos 字典。
        '''
        data = self.list if data is None else data
        if data is NoPaint:
            return NoPaint
        parts = path.split('.')
        if not parts:
            raise ValueError("Empty path")

        # 根节点名称必须匹配第一段
        if data.get('name') != parts[0]:
            raise KeyError(f"Root name mismatch: expected '{parts[0]}', got '{data.get('name')}'")

        current = data

        for i, part in enumerate(parts):
            # 检查当前节点名称是否匹配
            if current.get('name') != part:
                raise KeyError(f"Name mismatch: expected '{part}', got '{current.get('name')}'")

            # 最后一段
            if i == len(parts) - 1:
                return self.loader(current, part)

            # 不是最后一段，当前节点必须是布局
            if 'direction' not in current:
                raise KeyError(f"'{part}' is not a layout, cannot traverse further")

            next_name = parts[i + 1]
            found = None

            # 普通布局从 content 中查找
            found = self.subelement_finder(current, next_name)

            if found is None:
                raise KeyError(f"Child '{next_name}' not found in layout '{part}'")
            current = found

        # 正常流程不会执行到这里
        return None

    def loader(self, current, part):
        if 'direction' in current: # layout 类型
            return self.layout_loader(current, part)
        else:
            return self.widget_loader(current, part)

    def layout_loader(self, current, part):
        # 普通布局：返回 content 列表
        content = current.get('content')
        if content is None:
            raise ValueError(f"Layout '{part}' has no content")
        if not isinstance(content, list):
            raise TypeError(f"Layout '{part}' content is not a list")
        return content

    def widget_loader(self, current, part):
        # 控件：返回 content 属性
        content = current.get('content')
        if content is None:
            raise ValueError(f"Widget '{part}' has no content")
        return content

    def subelement_finder(self, current, next):
        # 普通布局从 content 中查找
        for child in current.get('content', []):
            if child.get('name') == next:
                found = child
                return found

    def show(self):   
        '''显示布局，返回布局对象；不需要绘制时返回 NoPaint。'''
        result = self.draw_layout()
        if result is NoPaint:
            return NoPaint
        return result[0]
        
    def draw_layout(self, list_content=None):
        '''绘制布局，返回布局对象和类型字符串；不需要绘制时返回 NoPaint。'''
        list_content = self.list if list_content is None else list_content
        if list_content is NoPaint:
            return NoPaint
        if list_content.get('direction') is not None: # 这是layout类型
            layout_info = self._layout_adding(list_content)
            if layout_info[0] is NoPaint:
                return NoPaint # 该布局不需要绘制
            if layout_info[1]:
                return layout_info[0] # 绘制布局
            else:
                layout = layout_info[0] # 布局对象
            result = self.add_layout(list_content, layout)
            if result is NoPaint:
                return NoPaint
            return result
        else: # 这是widget类型
            result = self.extend_widget(list_content)
            if result is NoPaint:
                return NoPaint
            return result
        
    def add_layout(self, list_content: Dict, layout: QLayout):
        self._for_loop(list_content, layout) # 递归绘制子布局
        self._add_stretch(list_content, layout) # 添加伸缩
        return self.return_layout(layout)
        
    def _for_loop(self, list_content, layout):
        for item in list_content['content']:
            widget = self.draw_layout(item)
            if widget is NoPaint:
                continue # 该节点不绘制
            if widget[1] == 'widget':
                func = layout.addWidget
            elif widget[1] == 'layout':
                func = layout.addLayout
            else:
                raise ValueError('Content must be a widget or a layout')
            adder = self.adder(widget)
            func(*adder[0], **adder[1])
            
    def _layout_adding(self, list_content):
        if list_content['direction'].lower() == 'h':
            return QHBoxLayout(), False
        elif list_content['direction'].lower() == 'v':
            return QVBoxLayout(), False
        else:
            return self.extend_layout(list_content), True
            
    def _add_stretch(self, list_content, layout):
        '''添加伸缩'''
        if list_content.get('stretch', False):
            layout.addStretch(1)
        
    def adder(self, widget) -> Tuple[QWidget | QLayout, Dict[str, Any]]:
        '''
        控制添加组件的返回值，可以在不复制draw_layout()函数的情况下，直接在原布局上添加加载时代码
        
        参数:
            widget: 控件或布局对象

        返回:
            返回一个元组，第一个元素是args内容，第二个元素是kwargs内容。可以自定义添加函数，如替换变量、函数调用等。
        '''
        return (widget[0], ), {}
    
    def return_layout(self, layout):
        '''
        返回布局对象和类型字符串，可以在不复制draw_layout()函数的情况下，直接在原布局上添加加载时代码
        参数:
            layout: 布局对象
        返回:
            返回一个元组，内容自定义；返回 NoPaint 表示该布局不绘制。
        '''
        return layout, 'layout' # 返回布局对象和类型字符串
    
    def extend_layout(self, list_info):
        '''扩展布局，可以在不复制draw_layout()函数的情况下，直接在原布局上添加加载时代码；返回 NoPaint 表示该布局不绘制'''
        UIMLException.direction_error(list_info['direction'].lower()) # 默认这里抛出错误，因为widget类型没有direction属性
        
    def extend_widget(self, widget_info):
        '''扩展控件，可以在不复制draw_layout()函数的情况下，直接在原控件上添加加载时代码；返回 NoPaint 表示该控件不绘制'''
        return widget_info['content'], 'widget'
            
class UIMLException(Exception):
    @staticmethod
    def direction_error(direction):
        '''错误方案：在widget类型中找不到direction属性时，抛出错误。可以自定义添加函数，如替换变量、函数调用等。'''
        raise UIMLException(f'Cannot load direction "{direction}" in class uiml::layout')
