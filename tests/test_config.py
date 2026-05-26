from auth.config import Settings


def test_debug_release_is_false():
	"""Garante que DEBUG='release' é interpretado como falso."""
	settings = Settings(DEBUG='release')

	assert settings.DEBUG is False
