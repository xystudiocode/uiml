import uiml
from PySide6.QtWidgets import QWidget,QApplication,QPushButton, QLabel

uimlcode = '''
<layout direction="v">
    <myapi::QPushButton args=['123'] />
    <QPushButton args=['123'] />
    <QLabel args=['123'] />
    <myapi::QLabel args=['123'] />
</layout>
'''

@uiml.widget_parser_chain.add
def add_parser2(ui_data, namespace, additional):
    if ui_data['type'] == 'myapi::QPushButton':
        print('Read 2 Button')
        return {'name': ui_data.get('name', ''), 'content': QPushButton(*ui_data.get('args', []), **ui_data.get('kwargs', {}))}
    elif ui_data['type'] == 'myapi::QLabel':
        print('Read 2 Label')
        return {'name': ui_data.get('name', ''), 'content': QLabel(*ui_data.get('args', []), **ui_data.get('kwargs', {}))}

def add_parser(ui_data, namespace, additional):
    if ui_data['type'] == 'myapi::QPushButton':
        print('Read 1 Button')
        return {'name': ui_data.get('name', ''), 'content': QLabel(*ui_data.get('args'), **ui_data.get('kwargs', {}))}

def test_main():
    uiml.add_parser(uiml.ParserEnum.widget_parser, add_parser)

    uiml.add_used_key(uiml.UsedKeyEnum.widget, ['123', '456'])
    uiml.add_used_key(uiml.UsedKeyEnum.layout, ['789'])

    assert uiml.used_widget_key == uiml.default_used_widget_key + ['123', '456']
    assert uiml.used_layout_key == uiml.default_used_layout_key + ['789']

    app = QApplication()

    main_widget = QWidget()

    main_layout = uiml.UIMLLayout(uiml.compile_ui(uiml.xml_parse(uimlcode))).show()

    main_widget.setLayout(main_layout)

    main_widget.show()

    exit(app.exec())

if __name__ == '__main__':
    test_main()