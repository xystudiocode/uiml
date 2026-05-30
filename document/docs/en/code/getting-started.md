# Getting Started
## Installation
Install uiml using pip:

```bash
pip install uiml
```

## Creating a uiml File
A uiml file is an XML file used to define the layout, style, and signals of the interface. You can create a uiml file using any text editor. Here is a simple example:

```xml
<layout name="central_layout" direction="v">
<QLabel name="text" arg=["This is a label"] />
<layout name="bottom_layout" direction="h" stretch="true">
<QPushButton name="ok_button" arg=["Close the window"] style="selected" signals={"clicked": self.close} />
</layout>
</layout>
```

Then save the code as a uiml file, for example `central_layout.uiml`.

## Loading a uiml File
You can use the uiml library to load a uiml file and create an interface. Here is a simple example:

```python
import uiml

# Initialize the application
app = uiml.QApplication()
widget = uiml.QWidget()

# Load the uiml file
layout = uiml.UIMLLayout(uiml.compile_ui_file("central_layout.uiml")).show()  # Read the layout data from the file, then parse and render the layout

# Set the layout
widget.setLayout(layout)

# Show the interface
widget.show()

# Run the application
app.exec()
```

If it runs successfully, a window containing a label and a button will be displayed. Clicking the button will close the window.

It should display:

<img src="/imgs/demo/1.png" width="200px" />