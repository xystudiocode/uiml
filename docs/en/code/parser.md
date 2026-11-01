# Extended Features

::: tip Note
This page describes the recommended `Parser API`. Documentation for the old `Namespace API` is still available in [Customization (Old Version)](./custom.md); `Namespace API` is deprecated, so new projects should use the approach on this page.
:::

## Description

`Parser API` extends the `uiml` parsing and rendering flow by registering parsers; it no longer requires `set_namespace`.

::: warning Do not mix with the old API
When the old Namespace API is enabled (`enable_namespace_api()`), `compile_ui` and other parsing flows take the old code path first, and widget/layout parsers registered through `add_parser` will not run. For new projects, *use only `Parser API`*.
:::

## API comparison

| Item | Namespace API | Parser API |
| --- | --- | --- |
| API | `set_namespace` | `add_parser`, `add_used_key`, `set_config` |
| Separation of concerns | `set_namespace` bundles parser settings, software configuration, and other settings together | Parser settings, software configuration, and other settings are separated |
| Mechanism | Overrides the default parser | Registers functions, then executes them as a queue |
| Extensibility | Poor (cannot register two parsers at the same time) | Multiple parsers can be registered at the same time |
| Use case | Old projects, projects that cannot migrate | New projects |
| Deprecated | Yes | No |

## API overview

| API | Description |
| --- | --- |
| `uiml.add_parser(enum: ParserEnum, value: list[Callable] \| ControlEnum )` | Registers a parser; `value` can be a function or a `UIMLLayout` subclass; pass `uiml.ControlEnum.reset` to restore the default parser |
| `uiml.add_used_key(enum: UsedKeyEnum, keys: list[str] \| ControlEnum)` | Extends the fields that are automatically read and removed during widget/layout parsing; pass `uiml.ControlEnum.reset` to restore the default fields |
| `uiml.set_config(enum: ParamEnum, value: bool \| ControlEnum)` | Modifies global configuration |
| `uiml.ParserEnum` | Selects the parser type to register |
| `uiml.UsedKeyEnum` | Selects the field list to extend |
| `uiml.ParamEnum` | Selects the configuration item to modify |
| `uiml.ControlEnum` | Methods for special operations |
| `uiml.NoPaint` | Special return value: stop parsing and skip drawing; see "Special value NoPaint" below |

Available `ParserEnum` parser types:

| Value | Registered object signature | Description |
| --- | --- | --- |
| `replacer` | `func(value)` | Value replacer; strings in widget args, kwargs, `init_steps`, and signals pass through it |
| `widget_parser` | `func(ui_data, namespace, additional)` | Widget parser; returns `{'name': ..., 'content': QWidget, ...}`, `None`, or `NoPaint` |
| `layout_parser` | `func(ui_data, namespace, additional)` | Layout parser; returns a layout data dict, `None`, or `NoPaint` |
| `namespace_parser` | `func() -> dict` | Namespace parser; returns the namespace dict used during parsing |
| `uiml_class` | A `UIMLLayout` subclass, or `func(list_data) -> UIMLLayout \| NoPaint \| None` | Registers a custom `UIMLLayout` renderer class |

Available `UsedKeyEnum` field lists:

| Value | Description |
| --- | --- |
| `widget` | Fields returned by the widget parser |
| `layout` | Fields returned by the layout parser |

Available `ParamEnum` configuration items:

| Value | Description |
| --- | --- |
| `value_convert` | Allow variable/function conversion |
| `reverse_namespace` | Reverse the namespace stack order |
| `debug_mode` | Debug mode |

Available `ControlEnum` methods:

| Value | Description |
| --- | --- |
| `reset` | Restore the default parser, field list, or configuration item |

## Registering parsers

- Register with `uiml.add_parser`.
- If a parser returns `None`, it passes the work to the next parser; the parser chain runs in **reverse** registration order, so the most recently registered parser runs first.
- The first non-`None` result takes effect.

**For example:**
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
    return None  # Pass to the next parser (eventually the default parser)

uiml.add_parser(uiml.ParserEnum.widget_parser, my_widget_parser)
```

**You can also use the ParserChain decorator form directly; the example above is equivalent to:**

```python
@uiml.widget_parser_chain.add
def my_widget_parser(ui_data, namespace, additional):
    ...
```

**To restore the default behavior:**

```python
uiml.add_parser(uiml.ParserEnum.widget_parser, uiml.ControlEnum.reset)
```

Default parsers can be called directly, for example `uiml.default_widget_parser(...)`, `uiml.default_layout_parser(...)`, and `uiml.default_namespace_parser()`. This is suitable for temporary use, but not recommended within the Parser API.

## Special value NoPaint (do not draw)

`uiml.NoPaint` is a constant (a singleton of an empty class) meaning "this node has been handled, but it must not be painted to the window".

Its difference from `None`:

- `None`: the current parser does not handle it; continue with the next parser, and possibly fall back to the default parser.
- `NoPaint`: stop the parser chain immediately, do not fall back, and do not paint this node or its subtree.

Example of returning `NoPaint` from a parser:

```python
import uiml


def my_widget_parser(ui_data, namespace, additional):
    # Hide a specific button: do not create the widget and do not fall back to the default widget parser
    if ui_data.get('type') == 'QPushButton' and ui_data.get('name') == 'hidden_button':
        return uiml.NoPaint
    return None


uiml.add_parser(uiml.ParserEnum.widget_parser, my_widget_parser)
```

```python
def my_layout_parser(ui_data, namespace=None, additional=None):
    # Do not paint this layout or any of its children
    if str(ui_data.get('direction', '')).lower() == 'hidden':
        return uiml.NoPaint
    return uiml.default_layout_parser(ui_data, namespace, additional)


uiml.add_parser(uiml.ParserEnum.layout_parser, my_layout_parser)
```

Renderer classes can also return `NoPaint`:

- `extend_widget(widget_info)` returning `uiml.NoPaint`: do not paint this widget.
- `extend_layout(list_info)` returning `uiml.NoPaint`: do not paint this custom layout.
- `return_layout(layout)` returning `uiml.NoPaint`: do not paint this layout.
- A `ParserEnum.uiml_class` parser returning `uiml.NoPaint`: `uiml.UIMLLayout(...)` returns `uiml.NoPaint` directly.

When the root node should not be painted, `show()` also returns `uiml.NoPaint`; the caller should check it first:

```python
layout = uiml.UIMLLayout(data).show()
if layout is not uiml.NoPaint:
    window.setLayout(layout)
```

`uiml.UIMLLayout(uiml.NoPaint).find_widget(...)` also returns `uiml.NoPaint`.

`default_layout_parser` automatically skips `NoPaint` children in the content list, so a `NoPaint` returned by a custom layout parser never appears in the rendering result.

## Extending automatically read fields

The default implementations of `widget_parser` / `layout_parser` remove some fields from the returned result and pass them on to subsequent processing.

If your tags use custom fields, you can add them to the corresponding list with `add_used_key`, so that these added items are not passed to the `UIMLLayout` structure tree.

**For example:**

```python
uiml.add_used_key(uiml.UsedKeyEnum.widget, ['my_widget_key'])
uiml.add_used_key(uiml.UsedKeyEnum.layout, ['texts', 'inputs', 'combos'])
```

**Restore the default field lists:**

```python
uiml.add_used_key(uiml.UsedKeyEnum.widget, uiml.ControlEnum.reset)
uiml.add_used_key(uiml.UsedKeyEnum.layout, uiml.ControlEnum.reset)
```

### Default values:
- `UsedKeyEnum.widget`: `['name', 'type', 'args', 'kwargs', 'init_steps', 'signals', 'style']`
- `UsedKeyEnum.layout`: `['name', 'direction', 'content', 'stretch']`

## Changing global configuration

The Parser API uses `set_config` to modify configuration:

```python
uiml.set_config(uiml.ParamEnum.value_convert, True)       # Allow variable/function conversion
uiml.set_config(uiml.ParamEnum.reverse_namespace, True)   # Reverse the namespace stack order
uiml.set_config(uiml.ParamEnum.debug_mode, True)          # Debug mode
```

**Restore the selected item to its default configuration:**

```python
uiml.set_config(uiml.ParamEnum.value_convert, uiml.ControlEnum.reset)
```

### Default values:
- `reverse_namespace`: `False`
- `value_convert`: `True`
- `debug_mode`: `False`

## Custom UIMLLayout renderer classes

With the Parser API, you do not need to change the call site to use a custom renderer. First register a `UIMLLayout` subclass (or a factory function that returns a `UIMLLayout` instance) on `ParserEnum.uiml_class`:

```python
import uiml


class MyUIMLLayout(uiml.UIMLLayout):
    ...


uiml.add_parser(uiml.ParserEnum.uiml_class, MyUIMLLayout)

# This returns a MyUIMLLayout instance
layout = uiml.UIMLLayout(uiml.compile_ui_file('layout.uiml'))
layout.show()
```

**Notes:**

- The registered parser only applies when constructing `uiml.UIMLLayout(...)` directly; explicitly constructing `MyUIMLLayout(...)` is not affected.
- When registering a factory function, returning `None` means continue falling back; returning a non-`None` value that is not a `UIMLLayout` raises `TypeError`.
- - Using a factory function is recommended, because only then can you have flexible extension points.
- Constructing `uiml.UIMLLayout(...)` inside a parser is protected against infinite recursion.
- Restore the default renderer: `uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)`.

**Factory function example:**

```python
def my_uiml_class(list_data):
    if list_data.get('direction') == 't':
        return MyUIMLLayout(list_data)
    return None  # Use the default UIMLLayout

uiml.add_parser(uiml.ParserEnum.uiml_class, my_uiml_class)
```

### Extensible rendering methods

`UIMLLayout` provides the following overridable methods:

- `extend_layout(list_info)`: Handles custom layout directions other than `h` / `v`; must return `(render_result, 'widget' | 'layout')`.
- `extend_widget(widget_info)`: Modifies widget addition logic; returns `(widget_info['content'], 'widget')` by default.
- `adder(widget)`: Controls the arguments used when adding to the parent layout; returns `((widget[0],), {})` by default.
- `return_layout(layout)`: Controls the layout return value; returns `(layout, 'layout')` by default.
- `add_layout(list_content, layout)`: Controls the whole layout addition flow; calls `_for_loop` and `_add_stretch` internally.
- `_for_loop(list_content, layout)`: Iterates over and adds child items.
- `_add_stretch(list_content, layout)`: Adds stretch according to `stretch`.
- `find_widget(path, data=None)`: Looks up compiled data by dot-separated path.
- `subelement_finder(current, next)`: Finds the next child inside a layout.
- `loader(current, part)`: Handles the last path segment; dispatches to `layout_loader` or `widget_loader` by default.
- `layout_loader(current, part)` / `widget_loader(current, part)`: Return a layout's `content` list or a widget's `content`, respectively.

### Customizing find_widget

Implement an extension to the child-widget lookup for the special `t` layout:

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

## Complete example

Add a new layout direction `t`: one row with three columns for text, an input box, and a combo box.

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
    '''Parse the direction="t" layout; let other directions use other parsers.'''
    if str(ui_data.get('direction', '')).lower() != 't':
        return None  # Use other parsers

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

uiml.add_parser(uiml.ParserEnum.layout_parser, layout_parser) # Register the layout parser

class MyUIMLLayout(uiml.UIMLLayout):
    def subelement_finder(self, current, next): # Same as above: method for finding child widgets
        if str(current.get('direction', '')).lower() == 't':
            for child in current.get('inputs', []) + current.get('combos', []):
                if child.get('name') == next:
                    return child
            return None
        return super().subelement_finder(current, next)

    def layout_loader(self, current, part):
        if str(current.get('direction', '')).lower() == 't': # Same as above: method for loading child widgets
            return {
                'texts': current.get('texts', []),
                'inputs': current.get('inputs', []),
                'combos': current.get('combos', []),
            }
        return super().layout_loader(current, part)

    def extend_layout(self, list_info):
        if str(list_info.get('direction', '')).lower() == 't': # Extension method: handles layout rendering
            layout = TLayout()
            for text, input_item, combo in zip(list_info['texts'], list_info['inputs'], list_info['combos']):
                layout.add_row(text, input_item['content'], combo['content'])
            return layout, 'widget'
        return super().extend_layout(list_info)

uiml.add_parser(uiml.ParserEnum.uiml_class, MyUIMLLayout) # Register the custom renderer class (register the class directly)
```

**Or**:
```python
... # Unchanged above

class MyUIMLLayout(uiml.UIMLLayout):
    ... # Same as above: methods for finding child widgets

def my_uiml_parser(list_data):
    if str(list_info.get('direction', '')).lower() == 't':
        layout = TLayout()
    return None

uiml.add_parser(uiml.ParserEnum.uiml_class, my_uiml_parser) # Register the custom renderer class (factory function)
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

import main  # Register the Parser API parsers


if __name__ == '__main__':
    app = uiml.QApplication([])
    window = uiml.QWidget()

    # QLineEdit / QComboBox are provided to XML tag parsing through additional
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

If you want `uiml` to automatically find variables and functions in a local scope, pass those variables through `additional` instead; both `compile_ui` and `xml_parse` accept an `additional` parameter.

## Migrating from the old version

Main mapping between the old Namespace API and the new Parser API:

| Old (Namespace API) | New (Parser API) |
| --- | --- |
| `uiml.enable_namespace_api()` + `set_namespace(value_replace_func=...)` | `uiml.add_parser(uiml.ParserEnum.replacer, ...)` |
| `set_namespace(widget_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.widget_parser, ...)` |
| `set_namespace(layout_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.layout_parser, ...)` |
| `set_namespace(namespace_parser_func=...)` | `uiml.add_parser(uiml.ParserEnum.namespace_parser, ...)` |
| `set_namespace(additional_used_widget_key=...)` | `uiml.add_used_key(uiml.UsedKeyEnum.widget, ...)` |
| `set_namespace(additional_used_layout_key=...)` | `uiml.add_used_key(uiml.UsedKeyEnum.layout, ...)` |
| `set_namespace(reverse=..., enable_value_convert=..., is_debug=...)` | `uiml.set_config(uiml.ParamEnum.reverse_namespace / value_convert / debug_mode, ...)` |
| Subclass `UIMLLayout` and construct the subclass manually | `uiml.add_parser(uiml.ParserEnum.uiml_class, Subclass)` then construct `uiml.UIMLLayout(...)` |
