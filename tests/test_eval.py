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
