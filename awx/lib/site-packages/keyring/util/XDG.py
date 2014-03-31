import os
import functools

class Preference:
	"""
	A decorator wrapping a 'priority' classmethod
	"""
	def __init__(self, name):
		"""
		Create a decorator giving preference to XDG_CURRENT_DESKTOP of 'name'
		"""
		self.name = name

	def decorate(self, func):
		self.func = func
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs) * self.multiplier
		return wrapper
	__call__ = decorate

	@property
	def multiplier(self):
		matches = os.environ.get('XDG_CURRENT_DESKTOP') == self.name
		return 1.5 if matches else 1
