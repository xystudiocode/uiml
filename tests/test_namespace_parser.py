import pytest

import uiml


@pytest.fixture(autouse=True)
def reset_namespace_chains():
    '''每个用例前后都恢复命名空间/组件解析器的默认值。'''
    uiml.add_parser(uiml.ParserEnum.namespace_parser, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.widget_parser, uiml.ControlEnum.reset)
    yield
    uiml.add_parser(uiml.ParserEnum.namespace_parser, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.widget_parser, uiml.ControlEnum.reset)


def test_default_namespace_parser_returns_load_namespace():
    namespace = uiml.namespace_parser_chain.run()

    assert isinstance(namespace, dict)
    assert 'load_namespace' in namespace


def test_custom_namespace_parser_used_by_compile_ui():
    marker_namespace = {'MARKER': object()}
    namespace_calls = []
    seen = {}

    def namespace_parser():
        namespace_calls.append(True)
        return marker_namespace

    def widget_parser(ui_data, namespace, additional):
        seen['namespace'] = namespace
        return {'name': ui_data.get('name'), 'content': 'compiled'}

    uiml.add_parser(uiml.ParserEnum.namespace_parser, namespace_parser)
    uiml.add_parser(uiml.ParserEnum.widget_parser, widget_parser)

    result = uiml.compile_ui({'type': 'SomeWidget', 'name': 'target'})

    assert namespace_calls == [True]
    assert seen['namespace'] is marker_namespace
    assert result == {'name': 'target', 'content': 'compiled'}


def test_namespace_parser_fallthrough():
    default_namespace = uiml.namespace_parser_chain.run()

    uiml.add_parser(uiml.ParserEnum.namespace_parser, lambda: None)

    assert uiml.namespace_parser_chain.run() == default_namespace


def test_reset_restores_default_namespace_parser():
    uiml.add_parser(uiml.ParserEnum.namespace_parser, lambda: {'CUSTOM': True})
    assert uiml.namespace_parser_chain.run() == {'CUSTOM': True}

    uiml.add_parser(uiml.ParserEnum.namespace_parser, uiml.ControlEnum.reset)

    assert 'load_namespace' in uiml.namespace_parser_chain.run()
    assert uiml.namespace_parser_chain.funcs == uiml.namespace_parser_chain._default_funcs


def test_namespace_api_branch_uses_legacy_namespace_parser(monkeypatch):
    '''保留旧版 Namespace API：启用后仍然使用 set_namespace 设置的 namespace_parser。'''
    monkeypatch.setattr(uiml, 'namespace_api_enabled', True)
    monkeypatch.setattr(uiml, 'namespace_parser', lambda: {'LEGACY': True})

    assert uiml._run_namespace_parser() == {'LEGACY': True}
