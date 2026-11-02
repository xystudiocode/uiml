# 扩展功能

::: tip 提示
本页介绍推荐的 `Parser API`。旧版 `Namespace API` 的说明仍然保留在 [自定义（旧版本）](./custom.md)；`Namespace API` 已弃用，新项目建议直接使用本页的写法。
:::

## 描述

`Parser API` 通过注册解析器来扩展 `uiml` 的解析与渲染流程，不需要再使用 `set_namespace`。

::: warning 不要混用旧版 API
旧版 Namespace API 启用后（`enable_namespace_api()`），`compile_ui`等解析流程 会优先走旧版分支，此时通过 `add_parser` 注册的组件/布局解析器不会生效。新项目 *请只使用 `Parser API`*。
:::

## API 对比

| 项目 | Namespace API | Parser API |
| --- | --- | --- |
| API | `set_namespace` | `add_parser`、`add_used_key`、`set_config` |
| 功能分离性 | `set_namespace` 方法把解析器设置、软件配置等全包 | 解析器设置、软件配置等分离 |
| 原理 | 覆盖默认解析器 | 函数注册，然后按照队列执行 |
| 可扩展性 | 差（无法同时注册两个解析器） | 可以同时注册多个解析器 |
| 适用场景 | 老项目、无法迁移的项目 | 新版本的项目 |
| 是否弃用 | 是 | 否 |

## API 一览

| API | 说明 |
| --- | --- |
| `uiml.add_parser(enum: ParserEnum, value: list[Callable] \| ControlEnum )` | 注册解析器；`value` 可以是函数，也可以是 `UIMLLayout` 子类；传入 `uiml.ControlEnum.reset` 可恢复默认解析器 |
| `uiml.add_used_key(enum: UsedKeyEnum, keys: list[str] \| ControlEnum)` | 扩展组件/布局解析时自动读取并从结果中移除的字段；传入 `uiml.ControlEnum.reset` 可恢复默认字段 |
| `uiml.set_config(enum: ParamEnum, value: bool \| ControlEnum)` | 修改全局配置 |
| `uiml.ParserEnum` | 选择要注册的解析器类型 |
| `uiml.UsedKeyEnum` | 选择要扩展的字段列表 |
| `uiml.ParamEnum` | 选择要修改的配置项 |
| `uiml.ControlEnum` | 特殊操作的方法 |
| `uiml.NoPaint` | 特殊返回值：停止解析并跳过绘制，详见下文“特殊值 NoPaint” |

`ParserEnum` 可用的解析器类型：

| 值 | 注册对象的签名 | 说明 |
| --- | --- | --- |
| `replacer` | `func(value)` | 值替换器，组件参数、关键字参数、`init_steps`、信号等字符串都会经过它 |
| `widget_parser` | `func(ui_data, namespace, additional)` | 组件解析器，返回 `{'name': ..., 'content': QWidget, ...}`、`None` 或 `NoPaint` |
| `layout_parser` | `func(ui_data, namespace, additional)` | 布局解析器，返回布局数据字典、`None` 或 `NoPaint` |
| `namespace_parser` | `func() -> dict` | 命名空间解析器，返回解析时使用的命名空间字典 |
| `uiml_class` | `UIMLLayout` 子类，或 `func(list_data) -> UIMLLayout \| NoPaint \| None` | 注册自定义的 `UIMLLayout` 渲染类 |

`UsedKeyEnum` 可用的字段列表：

| 值 | 说明 |
| --- | --- |
| `widget` | 组件解析器返回的字段 |
| `layout` | 布局解析器返回的字段 |

`ParamEnum` 可用的配置项：

| 值 | 说明 |
| --- | --- |
| `value_convert` | 允许变量/函数转换 |
| `reverse_namespace` | 翻转命名空间堆栈顺序 |
| `debug_mode` | 调试模式 |

`ControlEnum` 可用的方法：

| 值 | 说明 |
| --- | --- |
| `reset` | 恢复默认解析器/字段列表/配置项 |

## 注册解析器

- 使用 `uiml.add_parser` 注册。
- 如果解析器返回 `None` 表示交给下一个解析器；解析链按注册顺序的**逆序**执行，也就是后注册的解析器先执。
- 第一个非 `None` 的结果生效。

**如：**
```python
import uiml
from PySide6.QtWidgets import QPushButton

def my_widget_parser(ui_data, namespace, additional):
    if ui_data.get('type') == 'myapi::QPushButton':
        return {
            'name': ui_data.get('name', ''),
            'content': QPushButton(
                *ui_data.get('args', []),
                **ui_data.get('kwargs', {}),
            ),
        }
    return None  # 交给下一个解析器（最终回退到默认解析器）

uiml.add_parser(uiml.ParserEnum.widget_parser, my_widget_parser)
```

**也可以直接使用 ParserChain 的装饰器写法，上面的例子等价于：**

```python
@uiml.widget_parser_chain.add
def my_widget_parser(ui_data, namespace, additional):
    ...
```

**需要恢复默认行为时：**

```python
uiml.add_parser(uiml.ParserEnum.widget_parser, uiml.ControlEnum.reset)
```

默认解析器可以直接调用，例如调用 `uiml.default_widget_parser(...)`、`uiml.default_layout_parser(...)`、`uiml.default_namespace_parser()`，适和临时使用，但不推荐在 Parser API 中使用。

## 特殊值 NoPaint（不绘制）

`uiml.NoPaint` 是一个常量（空类的单例），表示“这个节点已经处理完成，但不要绘制到窗口上”。

它和 `None` 的区别：

- `None`：当前解析器不处理，继续执行下一个解析器，最终可能回退到默认解析器。
- `NoPaint`：立即停止解析链，不再回退，并且该节点及其子树不会出现在窗口上。

解析器返回 `NoPaint` 的示例：

```python
import uiml


def my_widget_parser(ui_data, namespace, additional):
    # 隐藏指定的按钮：不创建控件，也不回退到默认组件解析器
    if ui_data.get('type') == 'QPushButton' and ui_data.get('name') == 'hidden_button':
        return uiml.NoPaint
    return None


uiml.add_parser(uiml.ParserEnum.widget_parser, my_widget_parser)
```

```python
def my_layout_parser(ui_data, namespace=None, additional=None):
    # 整个布局及其子项都不绘制
    if str(ui_data.get('direction', '')).lower() == 'hidden':
        return uiml.NoPaint
    return uiml.default_layout_parser(ui_data, namespace, additional)


uiml.add_parser(uiml.ParserEnum.layout_parser, my_layout_parser)
```

渲染类也可以返回 `NoPaint`：

- `extend_widget(widget_info)` 返回 `uiml.NoPaint`：不绘制该控件。
- `extend_layout(list_info)` 返回 `uiml.NoPaint`：不绘制该自定义布局。
- `return_layout(layout)` 返回 `uiml.NoPaint`：不绘制该布局。
- `ParserEnum.uiml_class` 的解析器返回 `uiml.NoPaint`：`uiml.UIMLLayout(...)` 直接得到 `uiml.NoPaint`。

根节点不需要绘制时，`show()` 也会返回 `uiml.NoPaint`，调用方应先判断：

```python
layout = uiml.UIMLLayout(data).show()
if layout is not uiml.NoPaint:
    window.setLayout(layout)
```

`uiml.UIMLLayout(uiml.NoPaint).find_widget(...)` 也会返回 `uiml.NoPaint`。

`default_layout_parser` 会自动跳过内容列表中的 `NoPaint` 子项，因此自定义布局解析器返回的 `NoPaint` 不会出现在绘制结果里。

## 扩展自动读取的字段

`widget_parser` / `layout_parser` 的默认实现会把部分的字段从返回结果中移除，并继续传给后续处理。

若你的标签使用了自定义字段，可以用 `add_used_key` 把它们加入对应列表，使这些添加的项目不会传递给 `UIMLLayout`的结构树

**如：**

```python
uiml.add_used_key(uiml.UsedKeyEnum.widget, ['my_widget_key'])
uiml.add_used_key(uiml.UsedKeyEnum.layout, ['texts', 'inputs', 'combos'])
```

**恢复默认字段列表：**

```python
uiml.add_used_key(uiml.UsedKeyEnum.widget, uiml.ControlEnum.reset)
uiml.add_used_key(uiml.UsedKeyEnum.layout, uiml.ControlEnum.reset)
```

### 默认值：
- `UsedKeyEnum.widget`：`['name', 'type', 'args', 'kwargs', 'init_steps', 'signals', 'style']`
- `UsedKeyEnum.layout`：`['name', 'direction', 'content', 'stretch']`

## 修改全局配置

Parser API 使用 `set_config` 修改配置：

```python
uiml.set_config(uiml.ParamEnum.value_convert, True)       # 允许变量/函数转换
uiml.set_config(uiml.ParamEnum.reverse_namespace, True)   # 翻转命名空间堆栈顺序
uiml.set_config(uiml.ParamEnum.debug_mode, True)          # 调试模式
```

**恢复选择项为默认配置：**

```python
uiml.set_config(uiml.ParamEnum.value_convert, uiml.ControlEnum.reset)
```

### 默认值：
- `reverse_namespace`: `False`
- `value_convert`: `True`
- `debug_mode`: `False`

## 自定义 UIMLLayout 渲染类

在 Parser API 中，不需要修改调用点来使用自定义渲染类。先把 `UIMLLayout` 子类（或返回 `UIMLLayout` 实例的工厂函数）注册到 `ParserEnum.uiml_class`：

```python
import uiml


class MyUIMLLayout(uiml.UIMLLayout):
    ...


uiml.add_parser(uiml.ParserEnum.uiml_class, MyUIMLLayout)

# 这里会得到 MyUIMLLayout 实例
layout = uiml.UIMLLayout(uiml.compile_ui_file('layout.uiml'))
layout.show()
```

**说明：**

- 只有直接构造 `uiml.UIMLLayout(...)` 时才会经过注册的解析器；显式构造 `MyUIMLLayout(...)` 不会受影响。
- 注册工厂函数时，返回 `None` 表示继续回退；返回非 `UIMLLayout` 的非 `None` 值会抛出 `TypeError`。
- - 荐用工厂函数注册，因为这样才能有灵活的扩展点。
- 解析器内部再次构造 `uiml.UIMLLayout(...)` 有递归保护，不会无限递归。
- 恢复默认渲染类：`uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)`。

**工厂函数示例：**

```python
def my_uiml_class(list_data):
    if list_data.get('direction') == 't':
        return MyUIMLLayout(list_data)
    return None  # 使用默认 UIMLLayout

uiml.add_parser(uiml.ParserEnum.uiml_class, my_uiml_class)
```

### 可扩展的渲染方法

`UIMLLayout` 默认提供以下可重写方法：

- `extend_layout(list_info)`：处理非 `h` / `v` 的自定义布局方向；需要返回 `(渲染结果, 'widget' | 'layout')`。
- `extend_widget(widget_info)`：修改组件的添加逻辑，默认返回 `(widget_info['content'], 'widget')`。
- `adder(widget)`：控制加入父布局时的参数，默认返回 `((widget[0],), {})`。
- `return_layout(layout)`：控制布局的返回值，默认返回 `(layout, 'layout')`。
- `add_layout(list_content, layout)`：控制整个布局的添加流程，内部调用 `_for_loop` 和 `_add_stretch`。
- `_for_loop(list_content, layout)`：遍历并添加子项。
- `_add_stretch(list_content, layout)`：根据 `stretch` 添加伸缩。
- `find_widget(path, data=None)`：按点分路径查找编译后的数据。
- `subelement_finder(current, next)`：在布局中查找下一级子项。
- `loader(current, part)`：处理路径最后一段；默认分派到 `layout_loader` 或 `widget_loader`。
- `layout_loader(current, part)` / `widget_loader(current, part)`：分别返回布局的 `content` 列表或控件的 `content`。

### 自定义 find_widget

实现对子组件查找追加 `t` 这个特殊布局的扩展：
```python
class MyUIMLLayout(uiml.UIMLLayout):
    def subelement_finder(self, current, next):
        if str(current.get('direction', '')).lower() == 't':
            for child in current.get('inputs', []) + current.get('combos', []):
                if child.get('name') == next:
                    return child
            return None
        return super().subelement_finder(current, next)

    def layout_loader(self, current, part):
        if str(current.get('direction', '')).lower() == 't':
            return {
                'texts': current.get('texts', []),
                'inputs': current.get('inputs', []),
                'combos': current.get('combos', []),
            }
        return super().layout_loader(current, part)
```

## 完整示例

新增一个布局方向 `t`：一行三列，分别放置文本、输入框和下拉框。

文件树：

```text
uiml_demo/
├── main.py
├── run.py
├── layout.uiml
└── style.qss
```

**layout.uiml**：

```xml
<layout name="layout" direction="v">
    <layout name="t_layout" direction="t">
        <texts values=['a', 'b'] />
        <inputs>
            <QLineEdit name="input_a" />
            <QLineEdit name="input_b" />
        </inputs>
        <combos>
            <QComboBox name="combo_a" init_steps=[{"name": "addItems", "args": [['a', 'b']]}] signals={'currentIndexChanged': lambda: print('combo_a changed')}/>
            <QComboBox name="combo_b" init_steps=[{"name": "addItems", "args": [['c', 'd']]}] signals={'currentIndexChanged': lambda: print('combo_b changed')}/>
        </combos>
    </layout>
    <QLabel name="label1" args=['Hello!'] style="bigger_text" />
</layout>
```

**main.py**：

```python
import uiml
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TLayout(QWidget):
    '''一行三列的自定义布局：文本、输入框、下拉框。'''

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)

    def add_row(self, text, input_widget, combo_widget):
        row = QHBoxLayout()
        row.addWidget(QLabel(text))
        row.addWidget(input_widget)
        row.addWidget(combo_widget)
        self._layout.addLayout(row)


def layout_parser(ui_data, namespace=None, additional=None):
    '''解析 direction="t" 的布局，其他方向交给其他解析器。'''
    if str(ui_data.get('direction', '')).lower() != 't':
        return None  # 使用其他解析器

    children = ui_data.get('content', [])
    texts = children[0].get('values', [])
    inputs = [uiml.compile_ui(item, namespace, additional) for item in children[1].get('content', [])]
    combos = [uiml.compile_ui(item, namespace, additional) for item in children[2].get('content', [])]
    return {
        'name': ui_data.get('name'),
        'direction': 't',
        'texts': texts,
        'inputs': inputs,
        'combos': combos,
    }

uiml.add_parser(uiml.ParserEnum.layout_parser, layout_parser) # 注册布局解析器

class MyUIMLLayout(uiml.UIMLLayout):
    def subelement_finder(self, current, next): # 同上：处理寻找子组件的方法
        if str(current.get('direction', '')).lower() == 't':
            for child in current.get('inputs', []) + current.get('combos', []):
                if child.get('name') == next:
                    return child
            return None
        return super().subelement_finder(current, next)

    def layout_loader(self, current, part):
        if str(current.get('direction', '')).lower() == 't': # 同上：处理获取子组件的方法
            return {
                'texts': current.get('texts', []),
                'inputs': current.get('inputs', []),
                'combos': current.get('combos', []),
            }
        return super().layout_loader(current, part)

    def extend_layout(self, list_info):
        if str(list_info.get('direction', '')).lower() == 't': # 扩展方法：处理 layout 的绘制
            layout = TLayout()
            for text, input_item, combo in zip(list_info['texts'], list_info['inputs'], list_info['combos']):
                layout.add_row(text, input_item['content'], combo['content'])
            return layout, 'widget'
        return super().extend_layout(list_info)

uiml.add_parser(uiml.ParserEnum.uiml_class, MyUIMLLayout) # 注册自定义渲染类 (类直接挂载来更新)
```

**或**:
```python
... # 前面不变

class MyUIMLLayout(uiml.UIMLLayout):
    ... # 同上：处理寻找子组件的方法

def my_uiml_parser(list_data):
    if str(list_info.get('direction', '')).lower() == 't':
        layout = TLayout()
    return None

uiml.add_parser(uiml.ParserEnum.uiml_class, my_uiml_parser) # 注册自定义渲染类 (工厂函数)
```

**style.qss**：

```css
bigger_text {
    font-size: 16px;
}
```

**run.py**：

```python
import uiml
from PySide6.QtWidgets import QComboBox, QLineEdit

import main  # 注册 Parser API 解析器


if __name__ == '__main__':
    app = uiml.QApplication([])
    window = uiml.QWidget()

    # QLineEdit / QComboBox 通过 additional 提供给 XML 标签解析
    data = uiml.compile_ui_file(
        'layout.uiml',
        additional={'QLineEdit': QLineEdit, 'QComboBox': QComboBox},
    )
    layout = uiml.UIMLLayout(data).show()
    window.setLayout(layout)

    with open('style.qss', encoding='utf-8') as f:
        window.setStyleSheet(f.read())

    window.show()
    app.exec()
```

如果希望 `uiml` 自动找到命名空间中的变量和函数，可以把 `additional` 换成本地作用域中的变量；`compile_ui` 和 `xml_parse` 都支持 `additional` 参数。

## 从旧版本迁移

旧版 Namespace API 与新 Parser API 的主要对应关系：

| 旧版（Namespace API） | 新版（Parser API） |
| --- | --- |
| `uiml.enable_namespace_api()` + `set_namespace(value_replace_func=...)` | `uiml.add_parser(uiml.ParserEnum.replacer, ...)` |
| `set_namespace(widget_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.widget_parser, ...)` |
| `set_namespace(layout_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.layout_parser, ...)` |
| `set_namespace(namespace_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.namespace_parser, ...)` |
| `set_namespace(additional_used_widget_key=...)` | `uiml.add_used_key(uiml.UsedKeyEnum.widget, ...)` |
| `set_namespace(additional_used_layout_key=...)` | `uiml.add_used_key(uiml.UsedKeyEnum.layout, ...)` |
| `set_namespace(reverse=..., enable_value_convert=..., is_debug=...)` | `uiml.set_config(uiml.ParamEnum.reverse_namespace / value_convert / debug_mode, ...)` |
| 子类化 `UIMLLayout` 并手动构造子类 | `uiml.add_parser(uiml.ParserEnum.uiml_class, 子类)` 后构造 `uiml.UIMLLayout(...)` |
