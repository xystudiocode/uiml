# 自定义（旧版本）

::: warning 弃用提示
本页介绍旧版 Namespace API（`uiml.enable_namespace_api` / `uiml.set_namespace`）。该 API 仍然保留，用于兼容旧代码，但已弃用。新项目请使用 [自定义（新版本）](./parser.md) 中的 Parser API。
:::

## 描述

在旧版 API 中，你可以通过 `set_namespace` 注册自定义的替换、组件解析、布局解析和命名空间解析逻辑，并通过子类化 `UIMLLayout` 扩展布局渲染。

## 自定义参数

目前默认的自定义参数：

- `value_replace_func`：控制值的自动变换逻辑，默认不替换。
- `layout_parser_func`：控制在 `compile_ui` 时解析布局的逻辑。
- `widget_parser_func`：控制在 `compile_ui` 时解析组件的逻辑。
- `additional_used_widget_key`：设置扩展的 widget_key，方便读取，同时不会添加到参数。
- `additional_used_layout_key`：设置扩展的 layout_key 列表，方便读取，同时不会添加到参数。
- `namespace_parser_func`：控制解析命名空间的逻辑。
- `reverse`：控制解析作用域时的堆栈顺序。
- - 默认：`False`。
- - 如果设置为 `True`，则解析作用域时的堆栈顺序为从栈顶到栈底（栈底的作用域会覆盖栈顶的作用域）。
- - 如果设置为 `False`，则解析作用域时的堆栈顺序为从栈底到栈顶（栈底的作用域会覆盖栈顶的作用域）。
- `enable_value_convert`：控制是否在解析时进行值转换。
- - 默认：`True`（`enable_namespace_api()` 会开启值转换）。
- - 如果设置为 `False`，则解析时不会进行值转换。
- - 如果设置为 `True`，则解析时会进行值转换。
- `is_debug`：调试模式，默认 `False`。

::: tip 提示
`enable_value_convert` 只影响*外部变量或函数*，不影响 *Python 默认函数或变量*。
:::

这些自定义参数通过 `set_namespace` 设置。使用前必须先启用旧版 Namespace API：

```python
import uiml

uiml.enable_namespace_api()
uiml.set_namespace(
    layout_parser_func=layout_parser,
    widget_parser_func=widget_parser,
    namespace_parser_func=my_namespace_parser,
    enable_value_convert=True,
    reverse=False,
    is_debug=False,
)
```

::: tip 提示
`enable_namespace_api()` 会产生 `DeprecationWarning`。启用旧版 API 后，`compile_ui` 会走旧版分支，此时不要再与 Parser API 的 `add_parser` 混用。
:::

## 类的自定义

对于类的自定义，可以通过创建一个 `UIMLLayout` 的子类来实现，并手动构造这个子类。

默认提供了以下扩展方法：

- `UIMLLayout.extend_layout`：对于类型不是 `h` 或 `v` 的布局，可以在这里添加返回，默认报错。需要返回 `(渲染结果, 'widget' | 'layout')`。
- `UIMLLayout.extend_widget`：修改组件的添加逻辑，默认返回 `(widget_info['content'], 'widget')`。
- `UIMLLayout.adder`：控制在添加组件时候的参数，返回 `Tuple[QWidget | QLayout, Dict[str, Any]]`。
- `UIMLLayout.return_layout`：控制在添加布局时的返回值，默认返回 `(layout, 'layout')`。
- `UIMLLayout.add_layout`：控制添加布局的行为。
- - 子方法：`UIMLLayout._for_loop`：循环遍历添加子布局。
- - 子方法：`UIMLLayout._add_stretch`：添加伸缩条。
- `UIMLLayout.find_widget`：按点分路径查找编译后的数据；旧版示例通常会整体重写它。
- `UIMLLayout.subelement_finder`：在布局中查找下一级子项。
- `UIMLLayout.loader`：处理路径最后一段，默认分派到 `layout_loader` 或 `widget_loader`。
- `UIMLLayout.layout_loader` / `UIMLLayout.widget_loader`：分别返回布局的 `content` 列表或控件的 `content`。

::: tip 提示
旧版示例中完整重写的 `find_widget` 仍然可用，但新版推荐只重写 `subelement_finder` 和 `loader` 系列小钩子，避免复制整段 `find_widget`。新写法见 [自定义（新版本）](./parser.md) 的“自定义 find_widget”一节。
:::

## 特殊值 NoPaint

旧版解析器或渲染方法同样可以返回 `uiml.NoPaint`：该节点会停止解析并跳过绘制，等同当前版本的 `None`

## 示例

我要新增一个 layout 类型 `t`，它是一个自定义类 `TLayout`，对应一个通过 `add_row` 方法添加一行三列的布局：

- 需要有 3 个子参数，位于标签包围中，对应 `add_row` 的三个项目：一个字符串（不用写成 `QLabel`）、一个输入框、一个下拉框，分别是 `texts`、`inputs`、`combos`，用来创建一个布局。
- 在 `combos` 变化的时候发出提示。
- `texts` 的第一项、`inputs` 的第一项、`combos` 的第一项，对应 `add_row` 的第一列的三个参数。
- `texts` 的第二项、`inputs` 的第二项、`combos` 的第二项，对应 `add_row` 的第二列的三个参数，以此类推。

以下是使用旧版 Namespace API 的实现。

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


uiml.enable_namespace_api()  # 旧版 Namespace API 必须先启用


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
    '''解析 direction="t" 的布局，其他方向交给默认解析器。'''
    if str(ui_data.get('direction', '')).lower() != 't':
        return uiml.default_layout_parser(ui_data, namespace, additional)

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


uiml.set_namespace(layout_parser_func=layout_parser)


class MyUIMLLayout(uiml.UIMLLayout):
    def find_widget(self, path, data=None):
        data = self.list if data is None else data
        parts = path.split('.')

        if data.get('name') != parts[0]:
            raise KeyError(f"Root name mismatch: expected '{parts[0]}', got '{data.get('name')}'")

        current = data
        for i, part in enumerate(parts):
            if current.get('name') != part:
                raise KeyError(f"Name mismatch: expected '{part}', got '{current.get('name')}'")

            # 最后一段：返回布局 content 列表、控件内容，或 't' 布局的字段
            if i == len(parts) - 1:
                if 'direction' in current:
                    if str(current.get('direction', '')).lower() == 't':
                        return {
                            'texts': current.get('texts', []),
                            'inputs': current.get('inputs', []),
                            'combos': current.get('combos', []),
                        }
                    content = current.get('content')
                    if content is None:
                        raise ValueError(f"Layout '{part}' has no content")
                    if not isinstance(content, list):
                        raise TypeError(f"Layout '{part}' content is not a list")
                    return content

                content = current.get('content')
                if content is None:
                    raise ValueError(f"Widget '{part}' has no content")
                return content

            if 'direction' not in current:
                raise KeyError(f"'{part}' is not a layout, cannot traverse further")

            # 向下查找：'t' 布局从 inputs/combos 中查找，其他布局从 content 中查找
            next_name = parts[i + 1]
            found = None
            if str(current.get('direction', '')).lower() == 't':
                for child in current.get('inputs', []) + current.get('combos', []):
                    if child.get('name') == next_name:
                        found = child
                        break
            else:
                for child in current.get('content', []):
                    if child.get('name') == next_name:
                        found = child
                        break

            if found is None:
                raise KeyError(f"Child '{next_name}' not found in layout '{part}'")
            current = found

    def extend_layout(self, list_info):
        if str(list_info.get('direction', '')).lower() == 't':
            layout = TLayout()
            for text, input_item, combo in zip(list_info['texts'], list_info['inputs'], list_info['combos']):
                layout.add_row(text, input_item['content'], combo['content'])
            return layout, 'widget'
        return super().extend_layout(list_info)  # 未知方向由 UIMLLayout 抛出 UIMLException
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

import main  # 启用旧版 API，并调用 set_namespace 注册 layout_parser


if __name__ == '__main__':
    app = uiml.QApplication([])
    window = uiml.QWidget()

    # QLineEdit / QComboBox 通过 additional 提供给 XML 标签解析
    data = uiml.compile_ui_file(
        'layout.uiml',
        additional={'QLineEdit': QLineEdit, 'QComboBox': QComboBox},
    )
    # 旧版需要手动构造自定义子类
    layout = main.MyUIMLLayout(data).show()
    window.setLayout(layout)

    with open('style.qss', encoding='utf-8') as f:
        window.setStyleSheet(f.read())

    window.show()
    app.exec()
```

这样，你就能在旧版 API 中实现自定义布局和组件解析逻辑。迁移到推荐写法请参考 [自定义（新版本）](./parser.md)。
