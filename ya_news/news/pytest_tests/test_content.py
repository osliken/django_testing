import pytest

from django.conf import settings
from django.urls import reverse


@pytest.mark.django_db
def test_news_count(client, list_news):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, list_news_date):
    response = client.get(reverse('news:home'))
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, args_news, list_comments):
    response = client.get(reverse('news:detail', args=args_news))
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    assert all_comments[0].created < all_comments[1].created


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, args_news):
    response = client.get(reverse('news:detail', args=args_news))
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, args_news, author_client):
    response = client.get(reverse('news:detail', args=args_news))
    assert 'form' in response.context
