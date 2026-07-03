from typing import Any, Dict, Optional, Tuple
from uiml.uilib import *
import inspect
import re

skip_level=1

def load_namespace(check_global:bool=True, check_local: bool = False, reverse: bool=None, additional=None) -> Dict[str, Any]:
    '''
    获取当前调用方的命名空间（全局+局部变量合并）。

    参数:
        check_global: 是否检查全局命名空间。
        check_local: 是否检查局部命名空间。
    '''
    reverse = default_reverse if reverse is None else False
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if not value_convert:
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
        if (check_local and not(debug)):namespace.update(frame.f_locals)
    namespace.update(additional_value)  # 添加额外的值
    return namespace

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
        while idx < n and (xml_str[idx].isalnum() or xml_str[idx] == '_'):
            idx += 1
        if start == idx:
            raise ValueError('无效的标签名')
        return xml_str[start:idx]

    def parse_tag_name_only() -> str:
        nonlocal idx
        start = idx
        while idx < n and (xml_str[idx].isalnum() or xml_str[idx] == '_'):
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
        while idx < n:
            c = xml_str[idx]
            if c in '[{':
                depth += 1
            elif c in ']}':
                depth -= 1
            elif depth == 0 and (c.isspace() or c == '>' or (c == '/' and idx + 1 < n and xml_str[idx + 1] == '>')):
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
            while idx < n and (xml_str[idx].isalnum() or xml_str[idx] == '_'):
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
    
used_widget_key = ['name', 'type', 'args', 'kwargs', 'init_steps', 'signals', 'style']
used_layout_key = ['name', 'direction', 'content', 'stretch']

def set_namespace(value_replace_func=None, layout_parser_func=None, widget_parser_func=None, 
                  additional_used_widget_key=None, additional_used_layout_key=None,
                  namespace_parser_func=None, reverse=None, enable_value_convert=None,
                  is_debug=None
                ):
    '''
    设置解析函数/变量时使用的操作。
    '''
    global replacer, layout_parser, widget_parser, used_widget_key, used_layout_key, namespace_parser, default_reverse, value_convert, debug
    if value_replace_func is not None:replacer = value_replace_func
    if layout_parser_func is not None:layout_parser = layout_parser_func
    if widget_parser_func is not None:widget_parser = widget_parser_func
    if additional_used_widget_key is not None:used_widget_key.extend(additional_used_widget_key)
    if additional_used_layout_key is not None:used_widget_key.extend(additional_used_layout_key) # 设置需要解析的字段
    if namespace_parser_func is not None:namespace_parser = namespace_parser_func
    if reverse is not None:default_reverse = reverse
    if enable_value_convert is not None:value_convert = enable_value_convert
    if is_debug is not None:debug = is_debug
    
def default_replacer(value: str):
    '''默认替换函数，返回原值，可以自定义添加函数，如替换变量、函数调用等。'''
    return value

def default_layout_parser(ui_data: Dict[str, Any], namespace: Dict[str, Any]=None, additional=None):
    '''默认布局解析函数，进行递归解析返回'''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if namespace is None:namespace = namespace_parser() # 获取命名空间
    if ui_data is None: return {}
    
    other_values = _pop_dict(ui_data.copy(), used_layout_key)
    
    compiled_list = []
    for item in ui_data.get('content', []):
        ui = compile_ui(item, namespace, additional=additional_value) # 递归解析
        if ui is None:continue
        compiled_list.append(ui) # 递归解析
    return {'name': ui_data.get('name'), 'direction': ui_data.get('direction'), 'content': compiled_list, 'stretch': ui_data.get('stretch', False), **other_values}

def reg_replacer(value):
    if isinstance(value, str):
        return replacer(value)
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

def default_widget_parser(widget_data: Dict[str, Any], namespace: Dict[str, Any]=None, additional=None):
    '''默认控件解析函数，进行解析返回'''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if namespace is None:namespace = namespace_parser() # 获取命名空间
 
    argv = [] # 参数
    kwargv = {} # 关键字参数
    style = widget_data.get('style', '') # 样式
    
    for arg in widget_data.get('args', []):
        argv.append(reg_replacer(arg))
            
    for k, arg in widget_data.get('kwargs', {}).items():
        kwargv[k] = reg_replacer(arg)
                
    widget = eval(f'{widget_data.get('type')}(*{argv}, **{kwargv})', namespace|additional_value) # 获取函数
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

def compile_ui(ui_data, namespace=None, additional=None):
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    if namespace is None:namespace = namespace_parser() # 获取命名空间

    if ui_data.get('direction'): # 这是layout类型
        return layout_parser(ui_data, namespace, additional=additional_value)
    else: # 这是widget类型
        return widget_parser(ui_data, namespace, additional=additional_value)
    
def compile_ui_file(file_path: str, namespace=None, additional=None):
    '''
    从文件中读取扩展 XML 字符串并解析为 Python 字典，然后编译为布局或控件对象。

    参数:
        file_path: 文件路径，支持属性值不带引号、Python 字面量（列表、字典、集合）、变量/函数引用、表达式等。
        namespace: 解析函数/变量时使用的命名空间（默认为调用方的全局命名空间）。
    '''
    additional_value = {} if additional is None else additional  # 默认添加额外的空字典
    return compile_ui(xml_parse_file(file_path, namespace, additional=additional_value), namespace, additional=additional_value)  # 解析 XML 字符串并编译
    
class UIMLLayout:
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
        - 路径必须完整且精确，找不到时抛出 KeyError。

        参数:
            path: 点分隔的路径字符串，如 "layout.vlayout.checkbox2"
            data: 根字典（例如 {'name': 'layout', 'direction': 'h', 'content': [...]}）

        返回:
            根据路径找到的控件对象、布局的 content 列表，或 'u' 布局的 texts/inputs/combos 字典。
        '''
        data = self.list if data is None else data
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
                if 'direction' in current:
                    # 普通布局：返回 content 列表
                    content = current.get('content')
                    if content is None:
                        raise ValueError(f"Layout '{part}' has no content")
                    if not isinstance(content, list):
                        raise TypeError(f"Layout '{part}' content is not a list")
                    return content
                else:
                    # 控件：返回 content 属性
                    content = current.get('content')
                    if content is None:
                        raise ValueError(f"Widget '{part}' has no content")
                    return content

            # 不是最后一段，当前节点必须是布局
            if 'direction' not in current:
                raise KeyError(f"'{part}' is not a layout, cannot traverse further")

            next_name = parts[i + 1]
            found = None

            # 普通布局从 content 中查找
            for child in current.get('content', []):
                if child.get('name') == next_name:
                    found = child
                    break

            if found is None:
                raise KeyError(f"Child '{next_name}' not found in layout '{part}'")
            current = found

        # 正常流程不会执行到这里
        return None

    def show(self):   
        '''显示布局，返回布局对象和类型字符串'''
        return self.draw_layout()[0]
        
    def draw_layout(self, list_content=None):
        '''绘制布局，返回布局对象和类型字符串'''
        list_content = self.list if list_content is None else list_content
        if list_content.get('direction') is not None: # 这是layout类型
            layout_info = self._layout_adding(list_content)
            if layout_info[1]:
                return layout_info[0] # 绘制布局
            else:
                layout = layout_info[0] # 布局对象
            return self.add_layout(list_content, layout)
        else: # 这是widget类型
            return self.extend_widget(list_content)
        
    def add_layout(self, list_content: Dict, layout: QLayout):
        self._for_loop(list_content, layout) # 递归绘制子布局
        self._add_stretch(list_content, layout) # 添加伸缩
        return self.return_layout(layout)
        
    def _for_loop(self, list_content, layout):
        for item in list_content['content']:
            widget = self.draw_layout(item)
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
    
    def return_layout(layout):
        '''
        返回布局对象和类型字符串，可以在不复制draw_layout()函数的情况下，直接在原布局上添加加载时代码
        参数:
            layout: 布局对象
        返回:
            返回一个元组，内容自定义。
        '''
        return layout, 'layout' # 返回布局对象和类型字符串
    
    def extend_layout(self, list_info):
        '''扩展布局，可以在不复制draw_layout()函数的情况下，直接在原布局上添加加载时代码'''
        WidgetError.direction_error() # 默认这里抛出错误，因为widget类型没有direction属性
        
    def extend_widget(self, widget_info):
        '''扩展控件，可以在不复制draw_layout()函数的情况下，直接在原控件上添加加载时代码'''
        return widget_info['content'], 'widget'
            
class WidgetError:
    @staticmethod
    def direction_error():
        '''错误方案：在widget类型中找不到direction属性时，抛出错误。可以自定义添加函数，如替换变量、函数调用等。'''
        raise ValueError('Direction error: cannot find direction attribute in widget type')
    
set_namespace(
    default_replacer, default_layout_parser, default_widget_parser, 
    namespace_parser_func=load_namespace, reverse=False, 
    enable_value_convert=False, is_debug=False
) # 设置默认解析函数