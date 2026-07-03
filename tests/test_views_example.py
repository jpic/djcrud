import pytest
from django.urls import reverse

from djcrud_example.views_example.models import Article, Post

pytestmark = pytest.mark.tutorial


@pytest.mark.django_db
def test_views_list_renders_table_and_filter(client, admin_user):
    for i in range(6):
        Article.objects.create(
            title=f"Article {i}",
            body="body",
            category="news" if i % 2 == 0 else "blog",
        )
    client.force_login(admin_user)

    response = client.get(reverse("site:article:list"))
    assert response.status_code == 200
    content = response.content.decode()
    assert "Article 0" in content
    assert "category" in content.lower()


@pytest.mark.django_db
def test_views_search_filters_results(client, admin_user):
    Article.objects.create(title="News one", body="", category="news")
    Article.objects.create(title="Blog one", body="", category="blog")
    client.force_login(admin_user)

    response = client.get(reverse("site:article:list") + "?search=News")
    content = response.content.decode()
    assert "News one" in content
    assert "Blog one" not in content


@pytest.mark.django_db
def test_views_pagination(client, admin_user):
    for i in range(6):
        Article.objects.create(title=f"Row {i}", category="x")
    client.force_login(admin_user)

    response = client.get(reverse("site:article:list"))
    assert response.status_code == 200
    assert response.context["paginator"].per_page == 5
    assert response.context["paginator"].num_pages == 2
    assert 'max="2"' in response.content.decode()


@pytest.mark.django_db
def test_views_category_update_single_field(client, admin_user):
    article = Article.objects.create(title="Hello", body="text", category="news")
    client.force_login(admin_user)

    url = reverse("site:article:categoryupdate", args=[article.pk])
    response = client.get(url)
    assert response.status_code == 200
    form = response.context["form"]
    assert list(form.fields) == ["category"]

    client.post(url, {"category": "blog"})
    article.refresh_from_db()
    assert article.category == "blog"
    assert article.title == "Hello"


@pytest.mark.django_db
def test_views_publish_action(client, admin_user):
    article = Article.objects.create(title="Draft", published=False)
    client.force_login(admin_user)

    url = reverse("site:article:publish", args=[article.pk])
    assert client.get(url).status_code == 405
    response = client.post(url)
    assert response.status_code == 302
    article.refresh_from_db()
    assert article.published is True

    response = client.get(reverse("site:article:detail", args=[article.pk]))
    assert response.status_code == 200
    assert b"/publish/" not in response.content


@pytest.mark.django_db
def test_views_list_shows_custom_list_action(client, admin_user):
    Post.objects.create(title="Morning", category="news")
    client.force_login(admin_user)

    response = client.get(reverse("site:post:list"))
    assert response.status_code == 200
    assert b"Set category" in response.content


@pytest.mark.django_db
def test_views_bulk_set_category(client, admin_user):
    for title in ("A", "B"):
        Post.objects.create(title=title, category="news")
    client.force_login(admin_user)

    posts = list(Post.objects.order_by("pk"))
    url = (
        reverse("site:post:setcategory")
        + f"?pks={posts[0].pk}&pks={posts[1].pk}"
    )
    response = client.get(url)
    assert response.status_code == 200
    client.post(url, {"category": "blog", "next": reverse("site:post:list")})
    assert Post.objects.filter(category="blog").count() == 2