import pytest

import uiml


DATA = {'name': 'root', 'direction': 'v', 'content': []}


@pytest.fixture(autouse=True)
def reset_chains():
    '''每个用例前后恢复所有相关解析链。'''
    enums = (
        uiml.ParserEnum.widget_parser,
        uiml.ParserEnum.layout_parser,
        uiml.ParserEnum.uiml_class,
    )
    for enum in enums:
        uiml.add_parser(enum, uiml.ControlEnum.reset)
    yield
    for enum in enums:
        uiml.add_parser(enum, uiml.ControlEnum.reset)


def test_no_paint_is_a_constant_distinct_from_none():
    assert uiml.NoPaint is not None
    assert repr(uiml.NoPaint) == 'NoPaint'
    assert bool(uiml.NoPaint) is True


def test_parser_chain_stops_on_no_paint():
    calls = []

    def low_priority(ui_data, namespace, additional):
        calls.append('low')
        return {'name': ui_data.get('name'), 'content': 'low'}

    def high_priority(ui_data, namespace, additional):
        calls.append('high')
        return uiml.NoPaint

    # 后注册的先执行；返回 NoPaint 时必须停止，而不是像 None 一样回退
    uiml.add_parser(uiml.ParserEnum.widget_parser, low_priority)
    uiml.add_parser(uiml.ParserEnum.widget_parser, high_priority)

    assert uiml.compile_ui({'type': 'X', 'name': 'x'}) is uiml.NoPaint
    assert calls == ['high']


def test_widget_parser_no_paint_skips_child():
    def widget_parser(ui_data, namespace, additional):
        if ui_data.get('type') == 'Hidden':
            return uiml.NoPaint
        return {'name': ui_data.get('name'), 'content': 'widget'}

    uiml.add_parser(uiml.ParserEnum.widget_parser, widget_parser)

    compiled = uiml.compile_ui({
        'name': 'root',
        'direction': 'v',
        'content': [
            {'type': 'Hidden', 'name': 'hidden'},
            {'type': 'Visible', 'name': 'visible'},
        ],
    })

    assert [item['name'] for item in compiled['content']] == ['visible']


def test_layout_parser_no_paint_skips_child():
    def layout_parser(ui_data, namespace=None, additional=None):
        if str(ui_data.get('direction', '')).lower() == 'hidden':
            return uiml.NoPaint
        return uiml.default_layout_parser(ui_data, namespace, additional)

    uiml.add_parser(uiml.ParserEnum.layout_parser, layout_parser)

    compiled = uiml.compile_ui({
        'name': 'root',
        'direction': 'v',
        'content': [
            {'name': 'hidden_layout', 'direction': 'hidden', 'content': []},
            {'name': 'visible_layout', 'direction': 'h', 'content': []},
        ],
    })

    assert [item['name'] for item in compiled['content']] == ['visible_layout']


def test_default_layout_parser_skips_no_paint_directly():
    assert uiml.default_layout_parser(uiml.NoPaint) is uiml.NoPaint


def test_uiml_class_parser_can_return_no_paint():
    uiml.add_parser(uiml.ParserEnum.uiml_class, lambda data: uiml.NoPaint)

    assert uiml.UIMLLayout(DATA) is uiml.NoPaint


def test_show_and_find_widget_return_no_paint():
    layout = uiml.UIMLLayout(uiml.NoPaint)

    assert layout.show() is uiml.NoPaint
    assert layout.find_widget('root') is uiml.NoPaint


def test_for_loop_skips_no_paint():
    class FakeLayout:
        def __init__(self):
            self.items = []

        def addWidget(self, *args, **kwargs):
            self.items.append(('widget', args, kwargs))

        def addLayout(self, *args, **kwargs):
            self.items.append(('layout', args, kwargs))

    class SkipLayout(uiml.UIMLLayout):
        def draw_layout(self, list_content=None):
            if list_content['name'] == 'skip':
                return uiml.NoPaint
            return 'widget', 'widget'

    fake_layout = FakeLayout()
    SkipLayout(DATA)._for_loop(
        {'content': [{'name': 'skip'}, {'name': 'keep'}]},
        fake_layout,
    )

    assert fake_layout.items == [('widget', ('widget',), {})]


def test_renderer_hooks_can_return_no_paint():
    class HiddenWidgetLayout(uiml.UIMLLayout):
        def extend_widget(self, widget_info):
            return uiml.NoPaint

    class HiddenCustomLayout(uiml.UIMLLayout):
        def extend_layout(self, list_info):
            return uiml.NoPaint

    class HiddenReturnLayout(uiml.UIMLLayout):
        def _layout_adding(self, list_content):
            return object(), False

        def return_layout(self, layout):
            return uiml.NoPaint

    assert HiddenWidgetLayout({'name': 'w', 'type': 'X'}).draw_layout() is uiml.NoPaint
    assert HiddenCustomLayout({'name': 't', 'direction': 't', 'content': []}).draw_layout() is uiml.NoPaint
    assert HiddenReturnLayout({'name': 'h', 'direction': 'h', 'content': []}).draw_layout() is uiml.NoPaint
