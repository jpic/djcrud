# djcrud

**Faster Django development by getting more out of less.**

djcrud is a thin MVC layer on top of Django. Declare routers and views in
code, get secure CRUD and routing by default, and expose the view object
directly to templates.

Read the [philosophy](https://jpic.github.io/djcrud/philosophy.html) for the
full rationale.

## Install

```bash
pip install --pre djcrud
```

Note: The `--pre` flag is required for pre-release dependency versions.

See [installation](https://jpic.github.io/djcrud/install.html) for setup, or
try the [demo](https://jpic.github.io/djcrud/demo.html) to explore the example
project.

## Quick start

```python
# myapp/djcrud.py
import djcrud

from .models import YourModel


class YourModelRouter(djcrud.ModelRouter):
    model = YourModel


djcrud.site.routes.append(YourModelRouter)
```

```python
# urls.py
import djcrud

urlpatterns = djcrud.site.build().urlpatterns
```

Add `myapp` to `INSTALLED_APPS`. `build()` autodiscovers each app's `djcrud.py`
(like Django admin) — the import runs `routes.append()` before the route
registry is built.

## Documentation

- [Philosophy](https://jpic.github.io/djcrud/philosophy.html)
- [Install](https://jpic.github.io/djcrud/install.html)
- [Demo](https://jpic.github.io/djcrud/demo.html) — Try the example project
- [Tutorial](https://jpic.github.io/djcrud/tutorial/)
- [Reference](https://jpic.github.io/djcrud/reference/)

## Contributing

See the [contributing guide](https://jpic.github.io/djcrud/contributing.html)
for development setup, running tests, updating documentation screenshots, and
JavaScript conventions. Source: [`docs/contributing.rst`](docs/contributing.rst).

## License

MIT