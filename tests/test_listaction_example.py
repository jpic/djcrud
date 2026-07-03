import pytest
from django.urls import reverse

from djcrud_example.listaction_example.models import Post

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_list_shows_custom_list_action(client, admin_user):
    Post.objects.create(title="Morning", category="news")
    client.force_login(admin_user)

    response = client.get(reverse("site:post:list"))
    assert response.status_code == 200
    assert b"Set category" in response.content


@pytest.mark.django_db
def test_bulk_set_category(client, admin_user):
    for title in ("A", "B"):
        Post.objects.create(title=title, category="news")
    client.force_login(admin_user)

    posts = list(Post.objects.order_by("pk"))
    url = reverse("site:post:setcategory") + f"?pks={posts[0].pk}&pks={posts[1].pk}"
    response = client.get(url)
    assert response.status_code == 200
    client.post(url, {"category": "blog", "next": reverse("site:post:list")})
    assert Post.objects.filter(category="blog").count() == 2
