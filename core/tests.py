from datetime import date
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse

from . import views


class GoogleCalendarIntegrationTests(TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_connect_requires_google_configuration(self):
        response = self.client.get(reverse("google-calendar-connect"))

        self.assertRedirects(response, reverse("home"))

    @patch("core.views.requests.post")
    @patch("core.views.requests.get")
    @patch("core.views.get_holiday_events")
    def test_sync_creates_only_events_not_already_marked(self, holidays, get, post):
        new_holiday = {"date": date(2026, 9, 18), "title": "Independencia Nacional"}
        existing_holiday = {"date": date(2026, 9, 19), "title": "Glorias del Ejército"}
        holidays.return_value = [new_holiday, existing_holiday]

        list_response = Mock()
        list_response.json.return_value = {
            "items": [
                {
                    "extendedProperties": {
                        "private": {
                            "source_id": "2026-09-19:Glorias del Ejército",
                        }
                    }
                }
            ]
        }
        get.return_value = list_response
        post.return_value = Mock()

        created, skipped = views.sync_holidays_to_google_calendar(
            2026, {"Authorization": "Bearer token"}
        )

        self.assertEqual((created, skipped), (1, 1))
        self.assertEqual(post.call_count, 1)
        self.assertEqual(
            post.call_args.kwargs["json"]["start"], {"date": "2026-09-18"}
        )

    @patch("core.views.requests.delete")
    @patch("core.views.requests.get")
    def test_delete_removes_only_events_returned_by_the_app_filter(self, get, delete):
        get.return_value.json.return_value = {"items": [{"id": "event/id"}]}
        get.return_value.raise_for_status.return_value = None
        delete.return_value.raise_for_status.return_value = None

        deleted = views.delete_synced_holidays_from_google_calendar(
            {"Authorization": "Bearer token"}
        )

        self.assertEqual(deleted, 1)
        self.assertEqual(get.call_args.kwargs["params"]["privateExtendedProperty"], "source=calendario-chile")
        self.assertTrue(delete.call_args.args[0].endswith("/event%2Fid"))


class CalendarApiTests(TestCase):
    @patch.dict("os.environ", {"DJANGO_API_URL": "url/api/v1/"}, clear=True)
    @patch("core.views.requests.get")
    def test_invalid_api_url_does_not_request_or_hide_configuration_problem(self, get):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "No se pudieron cargar las fechas")
        get.assert_not_called()

    @patch.dict(
        "os.environ", {"DJANGO_API_URL": "https://example.test/api/v1/"}, clear=True
    )
    @patch("core.views.requests.get")
    @patch("core.views.cache.get", return_value=None)
    def test_api_endpoint_preserves_the_api_path(self, cache_get, get):
        get.return_value.json.return_value = []
        get.return_value.raise_for_status.return_value = None

        views.get_api_dates(2026)

        self.assertEqual(
            get.call_args.args[0], "https://example.test/api/v1/dates/2026"
        )
