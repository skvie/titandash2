from settings import get_active_state

from modules.bot.core.utilities import in_transition_func
from modules.bot.core.exceptions import ServerTerminationEncountered, TerminationEncountered

from functools import wraps

import random
import time


# Globally available properties dictionary, store information about functions
# and their options within the app. See "BotProperty" below.
_PROPERTIES = dict()


class BotProperty(object):
    """
    Queueable Function Decorator.
    """
    def __init__(self, queueable=False, forceable=False, shortcut=None, tooltip=None, interval=None, wrap_name=True):
        """
        Initialize the queueable decorator on a function, we should be able to choose
        a couple of options when making a function queueable, including whether ot not it
        is a function that should be "forced", the shortcut used and the tooltip displayed.

        :param queueable: Should this function be a queueable that can be queued by the bot.
        :param forceable: Should this function be forceable when called by the bot.
        :param shortcut: Specify a keyboard shortcut that can be used to queue the function.
        :param tooltip:  Specify a tooltip that will be displayed when the function is hovered over.
        :param interval: Specify an interval that will be used to derive scheduled function periodicity.
        :param wrap_name: Whether or not this function should also update the instances current function property when called.
        """
        self.queueable = queueable
        self.forceable = forceable
        self.shortcut = shortcut
        self.tooltip = tooltip
        self.interval = interval
        self.wrap_name = wrap_name

    def __call__(self, function):
        """
        Perform the magic required when this decorator is applied to our bot functions.
        """
        self._add_property(function=function)

        @wraps(function)
        def wrapper(bot, *args, **kwargs):
            """
            Wrap the bot property callable function.
            """
            # Before anything, perform a check to see if our server is still running.
            # Since instances run in separate threads, we need to know if we should
            # keep executing or not.
            if get_active_state() is False:
                # Raise a server termination error. Ensuring we can
                # catch and log our error properly.
                raise ServerTerminationEncountered()

            # Should this bot instance be terminated,
            # due to a manual termination.
            if bot._should_terminate:
                raise TerminationEncountered()

            # Ensure instance has its "Props" object updated to ensure
            # that the bot instance is saved and web sockets are sent.
            if self.wrap_name:
                bot.properties.function = function.__name__

            # Run our function normally once we've added it to our
            # globally available queueable dictionary.
            _ret = function(bot, *args, **kwargs)

            # Increment this bot properties usage on the instances
            # bot statistics that are available.
            bot.statistics.bot_statistics.increment_property(prop=function.__name__)

            # Return the _ret value only after we've executed
            # the function and incremented the property.
            return _ret

        # Returning wrapper function here, retain class decorator norms.
        return wrapper

    def _add_property(self, function):
        """
        Add the current function to the properties global variable with it's settings included.
        """
        if function.__name__ not in _PROPERTIES:
            _PROPERTIES[function.__name__] = {
                "name": function.__name__,
                "function": function,
                "queueable": self.queueable,
                "forceable": self.forceable,
                "shortcut": self.shortcut,
                "tooltip": self.tooltip,
                "interval": self.interval
            }

    @classmethod
    def _all(cls, function=None, queueables=False, forceables=False, shortcuts=False, intervals=False):
        """
        Utility function that attempts to grab all of the properties based on the options specified.
        """
        _all = {}
        results = []

        if function:
            try:
                _all = {
                   function: _PROPERTIES[function]
                }
            except KeyError:
                _all = {}
        else:
            _all.update(_PROPERTIES)

        for prop in _all.values():
            if shortcuts and prop["shortcut"]:
                results.append(prop)
                continue
            if queueables and prop["queueable"]:
                results.append(prop)
                continue
            if forceables and prop["forceable"]:
                results.append(prop)
                continue
            if intervals and prop["interval"]:
                results.append(prop)
                continue

        return results

    @classmethod
    def all(cls, function=None):
        return cls._all(function=function, queueables=True, forceables=True, shortcuts=True)

    @classmethod
    def queueables(cls, function=None, forceables=False):
        return cls._all(function=function, queueables=True, forceables=forceables)

    @classmethod
    def forceables(cls, function=None):
        return cls._all(function=function, forceables=True)

    @classmethod
    def shortcuts(cls, function=None):
        return cls._all(function=function, shortcuts=True)

    @classmethod
    def intervals(cls, function=None):
        return cls._all(function=function, intervals=True)


def not_in_transition(function, max_loops=30):
    """
    Stop functionality until some sort of game object is on the screen that represents the game not being
    in a transition state. If a transition state is detected, click the top of the screen a couple of
    times to attempt to change the state.

    Provide a max amount of loops before giving up and attempting to continue with bot functionality.
    """
    @wraps(function)
    def wrapped(*args, **kwargs):
        # Looping until max loops is reached or transition state
        # can be resolved successfully.
        in_transition_func(*args, max_loops=max_loops)
        # Run function normally afterwards.
        return function(*args, **kwargs)

    return wrapped


def wait_afterwards(function, floor, ceiling):
    """
    Delay a function after it's been called for a random amount of seconds between the specified floor and ceiling.
    """
    @wraps(function)
    def wrapped(*args, **kwargs):
        # Run function normally.
        function(*args, **kwargs)
        if ceiling:
            # Wait for a random amount of time after function finishes execution.
            time.sleep(random.randint(floor, ceiling))

    return wrapped