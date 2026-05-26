from auth.config import Settings


def test_debug_release_is_false():
	settings = Settings(DEBUG='release')

	assert settings.DEBUG is False
