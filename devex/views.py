from pprint import pformat
from django.http import HttpRequest
from django.shortcuts import render
from zmqgc import ZMQGrailClient as ChaliceClient

from django.conf import settings


def devex(request: HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    available_managers = cc.show_managers()
    

    selected_manager = request.GET.get("manager", None)

    selected_manager_params = {}

    try:
            params = cc.show_params(selected_manager).keys()
            for param in params:
                param_info = cc.get_parameter(selected_manager, param)
                selected_manager_params[param] = param_info
    except Exception as error:
            print(f"ERROR: {selected_manager}: {error}")

    selected_param = request.GET.get("param", None)
    selected_param_info = selected_manager_params[selected_param][selected_param] if selected_param else None
    fields_to_ignore = ["name", "description", "fitsname", "type"]
    selected_param_info = {k: v for k, v in selected_param_info.items() if k not in fields_to_ignore}
    
    return render(
        request,
        "devex/devex.html",
        context={
            "available_managers": available_managers,
            "selected_manager_params": selected_manager_params,
            "selected_manager": selected_manager,
            "selected_param": selected_param,
            "selected_param_info": pformat(selected_param_info),
        },
    )
