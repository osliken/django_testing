from http import HTTPStatus
from random import choice

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects, assertFormError

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


NEW_COMMENT = {'text': 'Новый комментарий'}


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, detail_args, form_data):
    initial_comments_count = Comment.objects.count()
    client.post(detail_args, data=form_data)
    comments_count = Comment.objects.count()
    assert initial_comments_count == comments_count


@pytest.mark.django_db
def test_user_can_create_comment(
    detail_args, author_client, author, form_data, news
):
    url = detail_args
    initial_comments_count = Comment.objects.count()
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    comments_count = Comment.objects.count()
    assert initial_comments_count + 1 == comments_count
    comment = Comment.objects.last()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(detail_args, author_client):
    bad_words_data = {
        'text': f'Какой-то текст, {choice(BAD_WORDS)}, еще текст'
    }
    initial_comments_count = Comment.objects.count()
    response = author_client.post(detail_args, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    comments_count = Comment.objects.count()
    assert initial_comments_count == comments_count


@pytest.mark.django_db
def test_author_can_delete_comment(args_comment, detail_args, author_client):
    initial_comments_count = Comment.objects.count()
    response = author_client.delete(reverse('news:delete', args=args_comment))
    assertRedirects(
        response,
        detail_args + '#comments'
    )
    comments_count = Comment.objects.count()
    assert initial_comments_count - 1 == comments_count


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(args_comment, admin_client):
    initial_comments_count = Comment.objects.count()
    response = admin_client.delete(reverse('news:delete', args=args_comment))
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert initial_comments_count == comments_count


@pytest.mark.django_db
def test_author_can_edit_comment(
    args_comment, detail_args, author_client, comment, news, author
):
    response = author_client.post(
        reverse('news:edit', args=args_comment),
        data=NEW_COMMENT
    )
    assertRedirects(
        response,
        detail_args + '#comments'
    )
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(
    args_comment, admin_client, comment, news, author
):
    response = admin_client.post(
        (reverse('news:edit', args=args_comment)), data=NEW_COMMENT
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    initial_comment = comment
    comment.refresh_from_db()
    assert initial_comment.text == comment.text
    assert initial_comment.news == news
    assert initial_comment.author == author
