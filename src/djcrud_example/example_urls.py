import djcrud


# definition by sub-class
class SubRouter(djcrud.Router):
    codename = "sub-router"
    routes = [
        # definition on-the-fly with clone
        djcrud.View.clone(
            codename="sub-view",
        ),
        djcrud.Router.clone(
            codename="sub-sub-router",
            routes=[
                djcrud.View.clone(
                    codename="sub-sub-view",
                )
            ],
        ),
    ]


# defining a root router
Site = djcrud.Router.clone(
    codename="router",
    routes=[
        djcrud.View.clone(
            codename="view",
        ),
        SubRouter,
    ],
)

# and urlpatterns to include
urlpatterns = Site().build().urlpatterns
