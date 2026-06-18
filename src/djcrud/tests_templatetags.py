from django.test import TestCase
from django.template import Context, Template


class EvalTemplateTagTest(TestCase):
    def test_eval_with_positional_args(self):
        """Test eval tag with positional arguments."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval my_func 10 20 as result %}"
            "{{ result }}"
        )

        def my_func(a, b):
            return a + b

        context = Context({'my_func': my_func})
        output = template.render(context)
        self.assertEqual(output.strip(), '30')

    def test_eval_with_kwargs(self):
        """Test eval tag with keyword arguments."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval my_func x=5 y=7 as result %}"
            "{{ result }}"
        )

        def my_func(x=0, y=0):
            return x * y

        context = Context({'my_func': my_func})
        output = template.render(context)
        self.assertEqual(output.strip(), '35')

    def test_eval_with_mixed_args(self):
        """Test eval tag with both positional and keyword arguments."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval my_func 10 multiplier=3 as result %}"
            "{{ result }}"
        )

        def my_func(base, multiplier=1):
            return base * multiplier

        context = Context({'my_func': my_func})
        output = template.render(context)
        self.assertEqual(output.strip(), '30')

    def test_eval_with_method(self):
        """Test eval tag with object method."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval obj.calculate 5 3 as result %}"
            "{{ result }}"
        )

        class Calculator:
            def calculate(self, a, b):
                return a + b

        context = Context({'obj': Calculator()})
        output = template.render(context)
        self.assertEqual(output.strip(), '8')

    def test_eval_with_string_kwargs(self):
        """Test eval tag with string keyword arguments."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval obj.greet name='World' as result %}"
            "{{ result }}"
        )

        class Greeter:
            def greet(self, name=''):
                return f'Hello, {name}!'

        context = Context({'obj': Greeter()})
        output = template.render(context)
        self.assertEqual(output.strip(), 'Hello, World!')

    def test_eval_with_context_variables(self):
        """Test eval tag with variables from context."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval my_func arg1 arg2 as result %}"
            "{{ result }}"
        )

        def my_func(a, b):
            return a - b

        context = Context({
            'my_func': my_func,
            'arg1': 100,
            'arg2': 25,
        })
        output = template.render(context)
        self.assertEqual(output.strip(), '75')

    def test_eval_result_stored_in_context(self):
        """Test that eval tag stores result in context variable."""
        template = Template(
            "{% load djcrud_tags %}"
            "{% eval my_func 42 as answer %}"
            "The answer is {{ answer }}"
        )

        def my_func(n):
            return n

        context = Context({'my_func': my_func})
        output = template.render(context)
        self.assertIn('42', output)
        self.assertIn('The answer is', output)
