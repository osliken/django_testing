from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutesForUser(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

    def test_pages_availability_for_anonymous_user(self):
        urls = (
            'notes:home', 'users:login', 'users:logout', 'users:signup'
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        urls = (
            'notes:list', 'notes:add', 'notes:success'
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.user_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)


class TestRoutesForAuthor(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Читатель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )

    def test_pages_availability_for_different_users(self):
        users_statuses = (
            (self.author_client, self.author, HTTPStatus.OK),
            (self.reader_client, self.reader, HTTPStatus.NOT_FOUND),
        )
        for client, user, status in users_statuses:
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(client=client, user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')

        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
