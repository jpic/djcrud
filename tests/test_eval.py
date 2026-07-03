from django.template import Template, Context


def test_eval():
    class Foo:
        def bar(self, *args, **kwargs):
            return "-".join(list(args) + [f"{k}-{v}" for k, v in kwargs.items()])

    template = Template("""
    {% load djcrud %}
    {% eval foo.bar "test" var some='kwarg' other=var as result %}
    {{ result }}
    """)
    context = Context(dict(foo=Foo(), var="2"))
    output = template.render(context)
    assert output.strip() == "test-2-some-kwarg-other-2"


def test_eval_missing_path_returns_none():
    template = Template("""
    {% load djcrud %}
    {% eval view.missing_method as result %}
    {{ result|default:"empty" }}
    """)
    context = Context({"view": object()})
    assert template.render(context).strip() == "empty"


def test_eval_non_callable_returns_value():
    template = Template("""
    {% load djcrud %}
    {% eval view.label as result %}
    {{ result }}
    """)

    class View:
        label = "heading"

    assert template.render(Context({"view": View()})).strip() == "heading"
