# Localization and Internationalization

This project uses Django's built-in i18n tools to support English and Russian interface text.

## Supported Languages

- English (`en`)
- Russian (`ru`)

The default language is English.

## Settings

Localization is configured in `booking_clone/settings/base.py`:

- `LANGUAGE_CODE = "en"`
- `LANGUAGES = [("en", "English"), ("ru", "Russian")]`
- `USE_I18N = True`
- `USE_TZ = True`
- `LOCALE_PATHS = [BASE_DIR / "locale"]`
- `django.middleware.locale.LocaleMiddleware`
- `django.template.context_processors.i18n`

`LocaleMiddleware` is placed after `SessionMiddleware` and before `CommonMiddleware`, which matches Django's recommended middleware order.

## Language Switching

Language switching is available through Django's built-in `set_language` view:

```text
POST /i18n/setlang/
```

The shared template `booking_clone/templates/base.html` includes a small language selector. It posts the selected language to the `set_language` endpoint and returns the user to the current page.

The demonstration page is available at:

```text
GET /localization/
```

## Template Translation Examples

Templates use Django i18n tags:

- `{% trans "Booking Clone" %}`
- `{% trans "Language" %}`
- `{% blocktrans %}...{% endblocktrans %}`

Files:

- `booking_clone/templates/base.html`
- `booking_clone/templates/localization/demo.html`

## Python Translation Examples

Model and admin metadata use `gettext_lazy`, for example:

- `CustomUser.email.verbose_name`
- `CustomUser.Meta.verbose_name`
- `Notification.event_type.verbose_name`
- App labels such as `Users`, `Bookings`, and `Notifications`

Validation and user-facing API strings were also prepared for translation, including:

- registration role validation
- login error messages
- booking date/status validation
- review rating validation
- booking action error messages
- SSE authorization messages

## Translation Files

Translation catalogs are stored in:

```text
booking_clone/locale/en/LC_MESSAGES/django.po
booking_clone/locale/ru/LC_MESSAGES/django.po
```

Compiled catalogs, when available, are stored as:

```text
booking_clone/locale/en/LC_MESSAGES/django.mo
booking_clone/locale/ru/LC_MESSAGES/django.mo
```

## Updating Translations

Run these commands from the `booking_clone/` directory:

```bash
python manage.py makemessages -l en -l ru
python manage.py compilemessages
```

If `compilemessages` fails, install GNU gettext for your system and run it again.

On macOS with Homebrew:

```bash
brew install gettext
brew link --force gettext
```

## Presentation Demonstration

1. Start the Django server.
2. Open `/localization/`.
3. Switch the language from English to Russian.
4. Show that visible template text changes.
5. Open Django admin and show translated model/app labels where available.
6. Trigger a validation error, such as invalid login or invalid review rating, while Russian is active.

This demonstrates both template-level and Python-code-level localization.
