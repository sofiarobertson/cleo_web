from django.http import HttpRequest
from django.shortcuts import render
from zmqgc import ZMQGrailClient as ChaliceClient

from django.conf import settings


def devex(request: HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    available_managers = cc.show_managers()

    selected_manager = "ScanCoordinator.ScanCoordinator"

    selected_manager_params = {}
    try:
        params = cc.show_params(selected_manager).keys()
        for param in params:
            param_info = cc.get_parameter(selected_manager, param)
            selected_manager_params[param] = param_info
    except Exception as error:
        print(f"ERROR: {selected_manager}: {error}")

    return render(
        request,
        "devex/devex.html",
        context={
            "available_managers": available_managers,
            "selected_manager_params": selected_manager_params,
            "selected_manager": selected_manager
        },
    )
