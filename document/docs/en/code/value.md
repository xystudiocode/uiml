# Parameters
## Layout
layout is a layout object that defines the components inside

- `name`: The name of the layout, which can be referenced in the code
- `direction`: The direction of the layout, which can be `v` (vertical) or `h` (horizontal), or it can be customized
- `stretch`: The stretch property of the layout, which can be `true` or `false`

## Widget
widget is a component object that defines the properties of the component

The tag name needs to be set to a Qt widget name, such as `QLabel`, `QPushButton`, etc.

- `name`: The name of the component, which can be referenced in the code
- `arg`: The arguments of the component, which can be a string, list, dictionary, etc.
- `kwarg`: The keyword arguments of the component, which can be a string, list, dictionary, etc.
- `init_steps`: The initialization steps of the component, which can be a list, for example `[{"name": "function", "arg": ["value"], "kwarg": {"style": "selected"}}]`
- `style`: The style class name of the component, which can be a string, for example `big_text`
- `signals`: The signals of the component, which can be a dictionary, for example `'clicked': self.close`