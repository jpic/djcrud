import djcrud

from .example_action import PublishView
from .example_listaction import post_router
from .example_listview import ArticleRouter

article_router = ArticleRouter.clone(routes=ArticleRouter.routes + [PublishView])

djcrud.site.routes.append(article_router)
djcrud.site.routes.append(post_router)