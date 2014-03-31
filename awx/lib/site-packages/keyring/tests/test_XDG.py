from mock import patch

from keyring.util import XDG

class TestPreference:
	@XDG.Preference('Unity')
	def one(self):
		return 1

	@patch.dict('os.environ', XDG_CURRENT_DESKTOP='KDE')
	def test_mismatch(self):
		assert self.one() == 1

	@patch.dict('os.environ', XDG_CURRENT_DESKTOP='Unity')
	def test_match(self):
		assert self.one() == 1.5
