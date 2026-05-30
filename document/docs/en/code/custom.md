# Customization

## Description
In `uiml`, you can modify its parsing logic by defining customizations, and you can add new replacement logic, etc.

## Custom Parameters
Currently, the default custom parameters are:
- `value_replace_func`: Controls the automatic value transformation logic; by default, it does not replace.
- `layout_parser_func`: Controls the logic for parsing layouts when using `compile_ui`.
- `widget_parser_func`: Controls the logic for parsing widgets when using `compile_ui`.

These custom parameters can be set using `uiml`'s `set_namespace` method.

## Customizing Classes

For class customization, you can achieve it by creating a subclass of `UIMLLayout`.

The following extended replacement methods are provided by default:
- `UIMLLayout.extend_layout`: For layouts whose type is not `h` or `v`, you can add them here; by default, it will raise an error.
- `UIMLLayout.extend_widget`: Modifies the logic for adding widgets.

You can also modify other methods, such as changing `UIMLLayout.find_widget` to alter the widget search logic, but this means you need to rewrite the entire function rather than simply extending the replacement.

## Example
I want to add a new layout type 't', which is a custom class `TLayout`, corresponding to a layout that adds a row with three columns using the `add_row` method:

- It needs three sub-parameters, located in the tag body, corresponding to the three items in `add_row`: a string (does not need to be written as QLabel), an input box, and a dropdown box — `texts`, `inputs`, `combos`, respectively, to create the layout.
- Emit a notification when `combos` changes.
- The first item of `texts`, the first item of `inputs`, and the first item of `combos` correspond to the three arguments of the first column in `add_row`.
- The second item of `texts`, the second item of `inputs`, and the second item of `combos` correspond to the three arguments of the second column in `add_row`, and so on.

The following is the code implementation:

File tree:
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
            <QComboBox name="combo_a" init_steps=[{"name": "addItems", "args": [['a', 'b']]}] signal={'currentIndexChanged': lambda: print('combo_a changed')}/>
            <QComboBox name="combo_b" init_steps=[{"name": "addItems", "args": [['c', 'd']]}] signal={'currentIndexChanged': lambda: print('combo_b changed')}/>
        </combos>
    </layout>
    <QLabel name="label1" args=['Hello!'] style="bigger_text" />
</layout>
<!--
This covers most common methods,
- Through init_steps: [{"name": "funtion_name", "args": [...], "kwargs": ...]}], you can implement initialization logic
- Through signal: {'currentIndexChanged': lambda: print('combo changed')}, you can implement prompts when the dropdown changes
- Through style: 'bigger_text', you can implement style modifications
-->
```

**main.py**:
```python
# In order to focus on the key points, let's not consider the implementation of this TLayout for now.
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

        # Index 0 -- String
        # Index 1 -- Input box
        # Index 2 -- Combo box
        inputs = ui_data['content'][1]
        for input in inputs['content']: # Parse inputs
            input_compiled_list.append(uiml.compile_ui(input)) # Recursively compile UI

        combos = ui_data['content'][2]
        combos_compiled_list = []
        for combo in combos['content']: # Parse combos
            combos_compiled_list.append(uiml.compile_ui(combo)) # Recursively compile UI
        return {'name': ui_data.get('name'), 'direction': ui_data.get('direction'), "texts": ui_data['content'][0]['values'], 'inputs': input_compiled_list, 'combos': combos_compiled_list} # Return the parsed layout data
    return uiml.default_layout_parser(ui_data) # Make it to default layout parser

uiml.set_namespace(layout_parser_func=layout_parser) # 设置自定义解析函数

class MyUIMLLayout(uiml.UIMLLayout):
    def __init__(self, list):
        super().__init__(list)

    # Extend find_widget to ensure combo and input are visible under the child elements of t_layout
    def find_widget(self, path: str, data=None):
        '''Find elements in a nested dictionary structure using a dot-separated path.

            Rules:
            - Each segment in the path corresponds to the 'name' field in the dictionary.
            - If the current node is a layout (contains the 'direction' key) and is not the last segment, automatically enter its child elements to continue the search.
            - Children of normal layouts (direction not 't') are in the 'content' list.
            - Children of special layouts (direction == 't') are in the 'inputs' and 'combos' lists ('texts' are not involved in navigation).
            - If the last segment is a normal layout, return its 'content' list; if it is a 'u' layout, return {'texts': ..., 'inputs': ..., 'combos': ...}; if it is a control, return its 'content'.
            - The path must be complete and exact; if not found, raise a KeyError.

            Parameters:
            path: dot-separated path string, e.g., "layout.vlayout.checkbox2"
            data: root dictionary (for example, {'name': 'layout', 'direction': 'h', 'content': [...]})

            Returns:
            The control object found by the path, the content list of a layout, or the texts/inputs/combos dictionary of a 'u' layout.
            '''
        data = self.list if data is None else data
        parts = path.split('.')
        if not parts:
            raise ValueError("Empty path")

        # Root name must match the first part
        if data.get('name') != parts[0]:
            raise KeyError(f"Root name mismatch: expected '{parts[0]}', got '{data.get('name')}'")

        current = data

        for i, part in enumerate(parts):
            # Check if the current node name matches the part
            if current.get('name') != part:
                raise KeyError(f"Name mismatch: expected '{part}', got '{current.get('name')}'")

            # Last segment
            if i == len(parts) - 1:
                if 'direction' in current:
                    direction = current.get('direction', '').lower()
                    if direction == 't':
                        # Special layout: return texts/inputs/combos dictionary
                        return {
                            'texts': current.get('texts', []),
                            'inputs': current.get('inputs', []),
                            'combos': current.get('combos', [])
                        }
                    else:
                        # Normal layout: return content list
                        content = current.get('content')
                        if content is None:
                            raise ValueError(f"Layout '{part}' has no content")
                        if not isinstance(content, list):
                            raise TypeError(f"Layout '{part}' content is not a list")
                        return content
                else:
                    # Widget: return content list
                    content = current.get('content')
                    if content is None:
                        raise ValueError(f"Widget '{part}' has no content")
                    return content

            # Not the last segment, enter child elements
            if 'direction' not in current:
                raise KeyError(f"'{part}' is not a layout, cannot traverse further")

            direction = current.get('direction', '').lower()
            next_name = parts[i + 1]
            found = None

            if direction == 't':
                # Find children in inputs and combos
                for child in current.get('inputs', []) + current.get('combos', []):
                    if child.get('name') == next_name:
                        found = child
                        break
            else:
                # Find children in content if it is a normal layout
                for child in current.get('content', []):
                    if child.get('name') == next_name:
                        found = child
                        break

            if found is None:
                raise KeyError(f"Child '{next_name}' not found in layout '{part}'")
            current = found

        # Normal flow will not reach here
        return None

    # Extend extend_layout to handle 't' layout
    def extend_layout(self, list_info):
        if list_info['direction'].lower() == 't':
            from uiStyles.widgets import UnitInputLayout
            layout = TLayout()
            for text, input, combo in zip(list_info['texts'], list_info['inputs'], list_info['combos']):
                text_show = get_lang(text[6:])
                layout.add_row(text_show, input['content'], combo['content'])
            return layout, 'layout'
        else:
            uiml.WidgetError.direction_error() # Make it to default layout parser
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
    # Initialize the application
    app = uiml.QApplication([])
    widget = uiml.compile_ui('layout.uiml')

    with open('style.qss', 'r') as f:
        widget.setStyleSheet(f.read()) # Load the style sheet
    
    # Load UI
    layout = main.MyUIMLLayout(compile_ui_file('layout.uiml'))  # Load configuration from file
    # This compile_ui_file function will automatically find the UI file and use the layout_parser_func set in main.py, as well as the default widget_parser_func and value_replace_func, so you don't need to set these parameters yourself
    widget.set_layout(layout)  # Set layout
    widget.show()  # Show application

    app.exec()  # Start application
```

In this way, you can implement custom layout and component parsing logic in `uiml`. You can extend and modify these methods as needed to meet your specific requirements.