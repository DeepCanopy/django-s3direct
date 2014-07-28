import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, resolve
from django.conf import settings
from django.test import TestCase

from s3direct import widgets, views


HTML_OUTPUT = (
    '<div class="s3direct" data-policy-url="/get_upload_params/">'
    '  <a class="file-link" target="_blank" href=""></a>'
    '  <a class="file-remove" href="#remove">Remove</a>'
    '  <input class="file-url" type="hidden" value="" id="None" name="filename" />'
    '  <input class="file-upload-to" type="hidden" value="foo">'
    '  <input class="file-input" type="file" />'
    '  <div class="progress progress-striped active">'
    '    <div class="bar"></div>'
    '  </div>'
    '</div>'
)

FOO_RESPONSE = {
    u'AWSAccessKeyId': u'',
    u'form_action': u'https://s3.amazonaws.com/test-bucket',
    u'success_action_status': u'201',
    u'acl': u'public-read',
    u'key': u'foo/${filename}',
    u'Content-Type': u'image/jpg'
}


class WidgetTest(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser('admin', 'u@email.com', 'admin')
        admin.save()

    def test_urls(self):
        reversed_url = reverse('s3direct')
        resolved_url = resolve('/get_upload_params/')
        self.assertEqual(reversed_url, '/get_upload_params/')
        self.assertEqual(resolved_url.view_name, 's3direct')

    def test_widget_html(self):
        widget = widgets.S3DirectWidget(upload_to='foo')
        self.assertEqual(widget.render('filename', None), HTML_OUTPUT)

    def test_widget_default_upload_to_html(self):
        widget = widgets.S3DirectWidget()
        html = HTML_OUTPUT.replace('foo', 's3direct')
        self.assertEqual(widget.render('filename', None), html)

    def test_signing_logged_in(self):
        self.client.login(username='admin', password='admin')
        data = {'upload_to': 'foo', 'name': 'image.jpg', 'type': 'image/jpg'}
        response = self.client.post(reverse('s3direct'), data)
        self.assertEqual(response.status_code, 200)

    def test_signing_logged_out(self):
        data = {'upload_to': 'foo', 'name': 'image.jpg', 'type': 'image/jpg'}
        response = self.client.post(reverse('s3direct'), data)
        self.assertEqual(response.status_code, 403)

    def test_signing_fields(self):
        self.client.login(username='admin', password='admin')
        data = {'upload_to': 'foo', 'name': 'image.jpg', 'type': 'image/jpg'}
        response = self.client.post(reverse('s3direct'), data)
        response_dict = json.loads(response.content.decode())
        self.assertTrue(u'signature' in response_dict)
        self.assertTrue(u'policy' in response_dict)
        self.assertDictContainsSubset(FOO_RESPONSE, response_dict)