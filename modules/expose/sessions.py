from db.models import BotInstance, SessionStatistics

import eel


@eel.expose
def sessions_information(selected_instance=None):
    """
    Grab all sessions information for a specific instance, or the default.
    """
    if selected_instance:
        # A specific instance was specified, use that instead of populating
        # an entire dictionary.
        instance = BotInstance.objects.get(pk=selected_instance)

        return {
            "pk": instance.pk,
            "name": instance.name,
            "sessions": SessionStatistics.objects.grab(instance=instance).json()
        }

    # Otherwise, go ahead with normal functionality
    # to retrieve information about all instances.
    dct = {"instances": []}

    # Looping through all instances, adding each one to the
    # dictionary of information.
    for instance in BotInstance.objects.all():
        dct["instances"].append({
            "pk": instance.pk,
            "name": instance.name,
            "sessions": SessionStatistics.objects.grab(instance=instance).json()
        })

    # Return our dictionary once all instances and their
    # appropriate information is available.
    return dct