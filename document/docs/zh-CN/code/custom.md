# 自定义

## 描述
在 `uiml` 中，你可以通过定义自定义来修改其解析逻辑，可以添加新的替换逻辑等。

## 自定义参数
目前默认的自定义参数：
- `value_replace_func`：控制值的自动变换逻辑，默认不替换。
- `layout_parser_func`: 控制在`compile_ui`时候，解析布局的逻辑。
- `widget_parser_func`: 控制在`compile_ui`时候，解析组件的逻辑。

这些自定义参数可以通过 `uiml` 的 `set_namespace` 方法来设置。

## 类的自定义

对于类的自定义，可以通过创建一个`UIMLLayout`的子类来实现。

默认提供了以下扩展替换方法：
- `UIMLLayout.extend_layout`：对于类型不是`h`或`v`的布局，可以在这里添加，默认报错。
- `UIMLLayout.extend_widget`：修改组件的添加逻辑。

还可以修改别的方法，比如修改`UIMLLayout.find_widget`修改组件查找逻辑，但是这意味着需要重写整个函数，而不是简单的扩展替换。

## 示例
我要新增一个layout类型't'，是一个自定义类"TLayout"，对应一个通过`add_row`方法添加一行三列的布局

- 需要有3个子参数，位于标签保卫中，对应`add_row`的三个项目：一个字符串（不用写成Qlabel），一个输入框，一个下拉框，分别是：`texts`, `inputs`, `combos`，来创建一个布局
- 在combos变化的时候发出提示
- texts的第一项，inputs的第一项，combos的第一项，对应`add_row`的第一列的三个参数
- texts的第二项，inputs的第二项，combos的第二项，对应`add_row`的第二列的三个参数，以此类推

以下是代码实现：

文件树：
```
uiml_demo/
├── main.py
├── run.py
├── layout.uiml
├── style.qss
```

**layout.uiml**:
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
<!-- 
这里涵盖了大部分常见的方法，
- 通过init_steps: [{"name": "funtion_name", "args": [...], "kwargs": ...]}}]，可以实现初始化逻辑
- 通过signals: {'currentIndexChanged': lambda: print('combo changed')}, 可以实现下拉框变化时的提示
- 通过style: 'bigger_text', 可以实现样式修改
-->
```

**main.py**:
```python
# 为了关注重点，先不考虑这个TLayout的实现
import uiml

def layout_parser(ui_data: Dict[str, Any]):
    '''
    自定义解析函数，用于解析layout类型为't'的布局。

    参数:
        ui_data: 布局数据字典，包含name、direction、content等字段。
        如果layout的direction是't'，则解析为TLayout，否则返回默认解析逻辑。
    '''
    if ui_data.get('direction').lower() == 't':
        input_compiled_list = []

        # 索引0 -- 字符串
        # 索引1 -- 输入框
        # 索引2 -- 选择框
        inputs = ui_data['content'][1]
        for input in inputs['content']: # 解析输入框
            input_compiled_list.append(uiml.compile_ui(input)) # 递归解析

        combos = ui_data['content'][2]
        combos_compiled_list = []
        for combo in combos['content']: # 解析选择框
            combos_compiled_list.append(uiml.compile_ui(combo)) # 递归解析
        return {'name': ui_data.get('name'), 'direction': ui_data.get('direction'), "texts": ui_data['content'][0]['values'], 'inputs': input_compiled_list, 'combos': combos_compiled_list} # 返回一个结构
    return uiml.default_layout_parser(ui_data) # 交由uiml进行默认替换

uiml.set_namespace(layout_parser_func=layout_parser) # 设置自定义解析函数

class MyUIMLLayout(uiml.UIMLLayout):
    def __init__(self, list):
        super().__init__(list)

    # 扩展find_widget，确保combo和input可见于t_layout的子元素下
    def find_widget(self, path: str, data=None):
        '''
        在嵌套字典结构中按点分隔路径查找元素。

        规则：
        - 路径中的每一段对应字典中的 'name' 字段。
        - 若当前节点是布局（含有 'direction' 键），且不是最后一段，则自动进入其子元素继续查找。
        - 普通布局（direction 非 't'）的子元素在 'content' 列表中。
        - 特殊布局（direction == 't'）的子元素在 'inputs' 和 'combos' 列表中（'texts' 不参与导航）。
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
                    direction = current.get('direction', '').lower()
                    if direction == 't':
                        # 特殊布局：返回 texts、inputs、combos 组成的字典
                        return {
                            'texts': current.get('texts', []),
                            'inputs': current.get('inputs', []),
                            'combos': current.get('combos', [])
                        }
                    else:
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

            direction = current.get('direction', '').lower()
            next_name = parts[i + 1]
            found = None

            if direction == 't':
                # 从 inputs 和 combos 中查找子元素
                for child in current.get('inputs', []) + current.get('combos', []):
                    if child.get('name') == next_name:
                        found = child
                        break
            else:
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

    # 扩展显示逻辑，确保能正常加载TLayout
    def extend_layout(self, list_info):
        if list_info['direction'].lower() == 't':
            from uiStyles.widgets import UnitInputLayout
            layout = TLayout()
            for text, input, combo in zip(list_info['texts'], list_info['inputs'], list_info['combos']):
                text_show = get_lang(text[6:])
                layout.add_row(text_show, input['content'], combo['content'])
            return layout, 'layout'
        else:
            uiml.WidgetError.direction_error() # 交由 uiml 进行处理
```

**style.qss**:
```css
bigger_text {
    font-size: 16px;
}
```

**run.py**:
```python
import uiml
import main

if __name__ == "__main__":
    # 初始化
    app = uiml.QApplication([])
    widget = uiml.compile_ui('layout.uiml')

    with open('style.qss', 'r') as f:
        widget.setStyleSheet(f.read()) # 加载样式
    
    # 加载ui
    layout = main.MyUIMLLayout(compile_ui_file('layout.uiml')) # 从文件中加载配置 这个compile_ui_file函数会自己寻找ui文件，并且会自动使用main.py中的设置的layout_parser_func,还有默认的widget_parser_func和value_replace_func，所以你不需要再设置这些参数了
    widget.set_layout(layout) # 设置布局
    widget.show() # 显示应用

    app.exec() # 启动应用
```

这样，你就能在 `uiml` 中实现自定义布局和组件解析逻辑了。你可以根据需要扩展和修改这些方法，以满足你的具体需求。