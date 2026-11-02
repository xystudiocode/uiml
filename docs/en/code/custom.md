# Customization (Old Version)

::: warning Deprecation notice
This page describes the old Namespace API (`uiml.enable_namespace_api` / `uiml.set_namespace`). It is retained for backward compatibility but is deprecated. New projects should use the Parser API described in [Customization (New Version)](./parser.md).
:::

## Description

With the old API, you can register custom replacement, widget parsing, layout parsing, and namespace parsing logic through `set_namespace`, and extend layout rendering by subclassing `UIMLLayout`.

## Custom parameters

The current default custom parameters are:

- `value_replace_func`: Controls the automatic value transformation logic; nothing is replaced by default.
- `layout_parser_func`: Controls the layout parsing logic in `compile_ui`.
- `widget_parser_func`: Controls the widget parsing logic in `compile_ui`.
- `additional_used_widget_key`: Sets extended widget keys for easy access without adding them to the arguments.
- `additional_used_layout_key`: Sets an extended layout key list for easy access without adding them to the arguments.
- `namespace_parser_func`: Controls the logic for parsing the namespace.
- `reverse`: Controls the stack order when parsing scopes.
- - Default: `False`.
- - If set to `True`, scopes are read from the top of the stack to the bottom (the scope at the bottom overrides the one at the top).
- - If set to `False`, scopes are read from the bottom of the stack to the top (the scope at the top overrides the one at the bottom).
- `enable_value_convert`: Controls whether value conversion is performed during parsing.
- - Default: `True` (`enable_namespace_api()` enables value conversion).
- - If set to `False`, no value conversion is performed.
- - If set to `True`, value conversion is performed.
- `is_debug`: Debug mode, `False` by default.

::: tip Note
`enable_value_convert` only affects *external variables or functions*; it does not affect *Python's default functions or variables*.
:::

These parameters are set with `set_namespace`. The old Namespace API must be enabled first:

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

::: tip Note
`enable_namespace_api()` emits a `DeprecationWarning`. Once the old API is enabled, `compile_ui` takes the old code path; do not mix it with the Parser API's `add_parser`.
:::

## Customizing classes

Class customization is done by creating a subclass of `UIMLLayout` and constructing that subclass manually.

The following extension methods are provided by default:

- `UIMLLayout.extend_layout`: For layouts whose direction is not `h` or `v`; it raises an error by default. It must return `(render_result, 'widget' | 'layout')`.
- `UIMLLayout.extend_widget`: Modifies widget addition logic; returns `(widget_info['content'], 'widget')` by default.
- `UIMLLayout.adder`: Controls the arguments used when adding a widget; returns `Tuple[QWidget | QLayout, Dict[str, Any]]`.
- `UIMLLayout.return_layout`: Controls the return value when adding a layout; returns `(layout, 'layout')` by default.
- `UIMLLayout.add_layout`: Controls the behavior of adding layouts.
- - Sub-method: `UIMLLayout._for_loop`: Iterates over and adds sub-layouts.
- - Sub-method: `UIMLLayout._add_stretch`: Adds stretch.
- `UIMLLayout.find_widget`: Looks up compiled data by dot-separated path; the old examples usually override the whole method.
- `UIMLLayout.subelement_finder`: Finds the next child inside a layout.
- `UIMLLayout.loader`: Handles the last path segment; dispatches to `layout_loader` or `widget_loader` by default.
- `UIMLLayout.layout_loader` / `UIMLLayout.widget_loader`: Return a layout's `content` list or a widget's `content`, respectively.

::: tip Note
The full `find_widget` override from the old examples still works, but the new version recommends overriding only the smaller `subelement_finder` and `loader` hooks instead of copying the whole method. See the "Customizing find_widget" section in [Customization (New Version)](./parser.md).
:::

## Special Value NoPaint

Older parsers or rendering methods can also return `uiml.NoPaint`: this node will stop parsing and skip drawing, which is equivalent to `None` in the current version.

## Example

We want to add a new layout direction `t`, represented by a custom class `TLayout` that adds a row with three columns through an `add_row` method:

- It needs 3 child parameters inside the tag body, corresponding to the three arguments of `add_row`: a string (does not need to be a `QLabel`), an input box, and a combo box — `texts`, `inputs`, and `combos`, respectively.
- Print a message when `combos` changes.
- The first item of `texts`, the first item of `inputs`, and the first item of `combos` correspond to the three arguments of the first column of `add_row`.
- The second item of `texts`, the second item of `inputs`, and the second item of `combos` correspond to the three arguments of the second column, and so on.

The following implementation uses the old Namespace API.

File tree:

```text
uiml_demo/
├── main.py
├── run.py
├── layout.uiml
└── style.qss
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
```

**main.py**:

```python
import uiml
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


uiml.enable_namespace_api()  # The old Namespace API must be enabled first


class TLayout(QWidget):
    '''A custom one-row, three-column layout: text, input, and combo box.'''

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
    '''Parse direction="t"; delegate other directions to the default parser.'''
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

            # Last segment: return a layout content list, widget content, or 't' layout fields
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

            # Descend: 't' layouts search inputs/combos, other layouts search content
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
        return super().extend_layout(list_info)  # Unknown directions raise UIMLException from UIMLLayout
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
from PySide6.QtWidgets import QComboBox, QLineEdit

import main  # Enables the old API and registers layout_parser via set_namespace


if __name__ == '__main__':
    app = uiml.QApplication([])
    window = uiml.QWidget()

    # Provide QLineEdit / QComboBox for XML tag parsing through additional
    data = uiml.compile_ui_file(
        'layout.uiml',
        additional={'QLineEdit': QLineEdit, 'QComboBox': QComboBox},
    )
    # The old version requires constructing the custom subclass manually
    layout = main.MyUIMLLayout(data).show()
    window.setLayout(layout)

    with open('style.qss', encoding='utf-8') as f:
        window.setStyleSheet(f.read())

    window.show()
    app.exec()
```

This is how custom layout and widget parsing works with the old API. For the recommended approach, see [Customization (New Version)](./parser.md).
