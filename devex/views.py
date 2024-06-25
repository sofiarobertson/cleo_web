from django.http import HttpRequest
from django.shortcuts import render
from zmqgc import ZMQGrailClient as ChaliceClient

from django.conf import settings



def get_available_managers(chalice_client: ChaliceClient):
    available_managers: list[str] = chalice_client.show_managers()
    major_managers = {}
    for manager in available_managers:
        major, minor = manager.split(".")
        if major == minor:
            major_managers[major] = []

        else:
            if major in major_managers:
                major_managers[major].append(minor)
            else:
                major_managers[major] = [minor]
    return major_managers


def get_params_for_manager(chalice_client: ChaliceClient, manager: str):
    selected_manager_params: dict[str, dict[str, dict]] = {}
    try:
        params = chalice_client.show_params(manager).keys()
        for param in params:
            param_info = chalice_client.get_parameter(manager, param)
            selected_manager_params[param] = param_info
    except Exception as error:
        print(f"ERROR: {manager}: {error}")

    return selected_manager_params


def get_samplers_for_manager(chalice_client: ChaliceClient, manager: str):
    selected_manager_samplers: dict[str, dict[str, dict]] = {}
    try:
        samplers = chalice_client.show_samplers(manager).keys()
        for sampler in samplers:
            sampler_info = chalice_client.get_sampler(manager, sampler)
            selected_manager_samplers[sampler] = sampler_info
    except Exception as error:
        print(f"ERROR: {manager}: {error}")

    return selected_manager_samplers





def devex(request: HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    major_managers = get_available_managers(cc)

    selected_manager = request.GET.get("manager", None)
    selected_param = request.GET.get("param", None)
    selected_paramfield = request.GET.get("paramfield", None)
    selected_param_info = None
    selected_paramfield_info = None
    selected_sampler = request.GET.get("sampler", None)
    selected_sampler_info = None
    selected_samplerfield = request.GET.get("samplerfield", None)
    selected_samplerfield_info = None


    selected_manager_params = get_params_for_manager(cc, selected_manager)

    if selected_param and selected_manager_params:
        selected_param_info = {
            k: v
            for k, v in selected_manager_params[selected_param].items()
            if k not in ["id", "name", "description", "type"]
        }
        is_struct = selected_manager_params[selected_param][selected_param].get("type", None) == "STRUCT"
        if is_struct:
            selected_param_info = {
                k: v
                for k, v in selected_param_info[selected_param].items()
                if k not in ["name", "description", "type", "fitsname"]
            }

    if selected_paramfield:
        selected_paramfield_info = selected_param_info[selected_paramfield]

    try:
            item = ["value"]
            selected_paramvalue = (
                {k: v for k, v in selected_paramfield_info.items() if k in item} if selected_paramfield_info else None
            )
    except Exception:
            selected_paramfield_info = selected_param_info.get(selected_paramfield, None) if selected_param_info else None
            selected_paramvalue = {"value": selected_paramfield_info}




    selected_manager_samplers = get_samplers_for_manager(cc, selected_manager)

    if selected_sampler and selected_manager_samplers:
        selected_sampler_info = {
            k: v
            for k, v in selected_manager_samplers[selected_sampler].items()
            if k not in ["id", "name", "description", "type"]
        }
        is_struct = selected_manager_samplers[selected_sampler][selected_sampler].get("type", None) == "STRUCT"
        if is_struct:
            selected_sampler_info = {
                k: v
                for k, v in selected_sampler_info[selected_sampler].items()
                if k not in ["name", "description", "type", "fitsname"]
            }

    if selected_samplerfield:
        selected_samplerfield_info = selected_sampler_info[selected_samplerfield]


    try:
            item = ["value"]
            selected_samplervalue = (
                {k: v for k, v in selected_samplerfield_info.items() if k in item} if selected_samplerfield_info else None
            )
    except Exception:
            selected_samplerfield_info = selected_sampler_info.get(selected_samplerfield, None) if selected_sampler_info else None
            selected_samplervalue = {"value": selected_paramfield_info}
    print(f"{selected_sampler=}")
    return render(
        request,
        "devex/devex.html",
        context={
            "major_managers": major_managers,
            "selected_manager_params": selected_manager_params,
            "selected_manager": selected_manager,
            "selected_param": selected_param,
            "selected_param_info": selected_param_info,
            "selected_paramfield": selected_paramfield,
            "selected_paramfield_info": selected_paramfield_info,
            "selected_paramvalue": selected_paramvalue,
            "selected_manager_samplers": selected_manager_samplers,
            "selected_sampler": selected_sampler,
            "selected_sampler_info": selected_sampler_info,
            "selected_samplerfield": selected_samplerfield,
            "selected_samplerfield_info": selected_samplerfield_info,
            "selected_samplervalue": selected_samplervalue,

        }
    )


# selected_manager_samplers = {}

    # try:
    #     samplers = cc.show_samplers(selected_manager).keys()
    #     for sampler in samplers:
    #         sampler_info = cc.get_sampler(selected_manager, sampler)
    #         selected_manager_samplers[sampler] = sampler_info
    # except Exception as error:
    #     print(f"ERROR: {selected_manager}: {error}")

#     selected_sampler = request.GET.get("sampler", None)
#     if selected_sampler and selected_sampler != "None":

#         selected_sampler_info = selected_manager_samplers[selected_sampler][selected_sampler] if selected_sampler else None
#         samplerfields_to_ignore = ["name", "fitsname", "type", "id", "description"]
#         selected_sampler_info = (
#             {k: v for k, v in selected_sampler_info.items() if k not in samplerfields_to_ignore}
#             if selected_sampler_info
#             else None
#         )

#         selected_samplerfield = request.GET.get("samplerfield", None)

#         try:
#             selected_samplerfield_info = (
#                 selected_sampler_info.get(selected_samplerfield, None) if selected_sampler_info else None
#             )
#             selected_samplerfield_info = (
#                 {k: v for k, v in selected_samplerfield_info.items() if k not in samplerfields_to_ignore}
#                 if selected_samplerfield_info
#                 else None
#             )
#             item = ["value"]
#             selected_sampler_value = (
#                 {k: v for k, v in selected_samplerfield_info.items() if k in item} if selected_samplerfield_info else None
#             )
#         except Exception:
#             selected_samplerfield_info = (
#                 selected_sampler_info.get(selected_samplerfield, None) if selected_sampler_info else None
#             )
#             selected_sampler_value = {"value": selected_samplerfield_info}
#     else:
#         selected_sampler_info = None
#         selected_samplerfield = None
#         selected_samplerfield_info = None
#         selected_sampler_value = None
#     print(f"{selected_paramfield=}")
#     return render(
#         request,
#         "devex/devex.html",
#         context={
#             "available_managers": available_managers,
#             "major_managers": major_managers,
#             "selected_manager_params": selected_manager_params,
#             "selected_manager": selected_manager,
#             "selected_param": selected_param,
#             "selected_param_info": selected_param_info,
#             "selected_paramfield": selected_paramfield,
#             "selected_paramfield_info": selected_paramfield_info,
#             "selected_value": selected_value,
#             "selected_manager_samplers": selected_manager_samplers,
#             "selected_sampler": selected_sampler,
#             "selected_sampler_info": selected_sampler_info,
#             "selected_samplerfield": selected_samplerfield,
#             "selected_samplerfield_info": selected_samplerfield_info,
#             "selected_sampler_value": selected_sampler_value,
#         },
#     )
