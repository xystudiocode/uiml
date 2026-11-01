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

def test_add_parser():
    uiml.add_parser(uiml.ParserEnum.widget_parser, add_parser)

def test_add_used_key():
    uiml.add_used_key(uiml.UsedKeyEnum.widget, ['123', '456'])
    uiml.add_used_key(uiml.UsedKeyEnum.layout, ['789'])

    assert uiml.used_widget_key == uiml.default_used_widget_key + ['123', '456']
    assert uiml.used_layout_key == uiml.default_used_layout_key + ['789']

def test_add_error_parser():
    try:
        uiml.add_parser(uiml.UsedKeyEnum.widget, add_parser2)

        raise AssertionError
    except ValueError as e:
        pass

def test_reset():
    uiml.add_used_key(uiml.UsedKeyEnum.widget, uiml.ControlEnum.reset)
    uiml.replacer_chain.reset()

    assert uiml.used_widget_key == uiml.default_used_widget_key
    assert uiml.replacer_chain.funcs == uiml.replacer_chain._default_funcs

def test_config():
    uiml.set_config(uiml.ParamEnum.reverse_namespace, True)
    uiml.set_config(uiml.ParamEnum.debug_mode, False)

    assert uiml.config['reverse_namespace'] == True
    assert uiml.config['debug_mode'] == False

    uiml.set_config(uiml.ParamEnum.reverse_namespace, uiml.ControlEnum.reset)

    assert uiml.config['reverse_namespace'] == uiml.default_config['reverse_namespace']
