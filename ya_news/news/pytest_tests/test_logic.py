from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


NEW_COMMENT = {'text': 'Новый комментарий'}


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, args_news, form_data):
    client.post(
        reverse('news:detail', args=args_news),
        data=form_data
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_can_create_comment(
    args_news, author_client, author, form_data, news
):
    url = reverse('news:detail', args=args_news)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert comments_count == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(args_news, author_client):
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(
        reverse('news:detail', args=args_news),
        data=bad_words_data
    )
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_author_can_delete_comment(args_comment, args_news, author_client):
    response = author_client.delete(reverse('news:delete', args=args_comment))
    assertRedirects(
        response,
        reverse('news:detail', args=args_news) + '#comments'
    )
    comments_count = Comment.objects.count()
    assert comments_count == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(args_comment, admin_client):
    response = admin_client.delete(reverse('news:delete', args=args_comment))
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


@pytest.mark.django_db
def test_author_can_edit_comment(
    args_comment, args_news, author_client, comment
):
    response = author_client.post(
        reverse('news:edit', args=args_comment),
        data=NEW_COMMENT
    )
    assertRedirects(
        response,
        reverse('news:detail', args=args_news) + '#comments'
    )
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT['text']


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(
    args_comment, admin_client, comment
):
    response = admin_client.post(
        (reverse('news:edit', args=args_comment)), data=NEW_COMMENT
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == comment.text
