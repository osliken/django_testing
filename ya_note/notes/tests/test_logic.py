from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
URL_SUCCESS = reverse('notes:success')
URL_ADD = reverse('notes:add')


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_user_can_create_note(self):
        url = URL_ADD
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, URL_SUCCESS)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        url = URL_ADD
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_empty_slug(self):
        url = URL_ADD
        self.form_data.pop('slug')
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertRedirects(response, URL_SUCCESS)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNote(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатель')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }

    def test_not_unique_slug(self):
        url = URL_ADD
        self.form_data['slug'] = self.note.slug
        self.client.force_login(self.author)
        response = self.client.post(url, data=self.form_data)
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url, self.form_data)
        self.assertRedirects(response, URL_SUCCESS)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])
        self.assertEqual(self.note.author, self.author)

    def test_other_user_cant_edit_note(self):
        url = reverse('notes:edit', args=(self.note.slug,))
        self.client.force_login(self.reader)
        response = self.client.post(url, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
        self.assertEqual(self.note.author, self.author)

    def test_author_can_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.author)
        response = self.client.post(url)
        self.assertRedirects(response, URL_SUCCESS)
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        url = reverse('notes:delete', args=(self.note.slug,))
        self.client.force_login(self.reader)
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
