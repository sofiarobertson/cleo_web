from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from zmqgc import ZMQGrailClient as ChaliceClient
from tortoise.models import History, ObsProcedure, ObsProjectRef, Observer, Operator
from django.views import generic
from django.conf import settings



def info(request):
    histories = History.objects.order_by("-datetime")[:10]

    return render(
            request,
            "devex/script.html",
            context={
                "histories": histories,
            }
        )


def status_info(request):
    history = History.objects.order_by("datetime").last()
    return render(
            request,
            "devex/status.html",
            context={
                "history": history,
            },
        )


class HistoryDetailView(generic.DetailView):
    model = History
    template_name = "devex/history_detail.html"
    context_object_name = "history"

class HistoryDetailView2(generic.DetailView):
    model = History
    template_name = "devex/history_detailstatus.html"
    context_object_name = "history"


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


def get_param_value(request, manager, param, field=None):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    try:
        param_info = cc.get_parameter(manager, param)
        if field:
            value_call = param_info[param].get(field)
            value = value_call.get("value")
        else:
            value = param_info[param].get("value")
    except Exception as error:
        value = "error"
        print(f"ERROR:{manager}.{param}.{field}:{error}")

    return render(request, "devex/param_value.html", context={"value": value})


def get_sampler_value(request, manager, sampler, field=None):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    try:
        sampler_info = cc.get_sampler(manager, sampler)
        if field:
            value_call = sampler_info[sampler].get(field)
            value = value_call.get("value")
        else:
            value = sampler_info[sampler].get("value")
    except Exception as error:
        value = "error"
        print(f"ERROR:{manager}.{sampler}.{field}:{error}")

    return render(request, "devex/sampler_value.html", context={"value": value})


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
        foo = selected_manager_samplers[selected_sampler]
        try:
            foo[selected_sampler].get("type", None) == "STRUCT"
        except AttributeError:
            selected_sampler_info = {"nope": "TBD"}

        else:
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
        selected_samplerfield_info = (
            selected_sampler_info.get(selected_samplerfield, None) if selected_sampler_info else None
        )
        selected_samplervalue = {"value": selected_samplerfield_info}

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
        },
    )


def get_device(request, manager):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    manager = "ScanCoordinator"
    selected_manager_params = get_params_for_manager(cc, manager)
    subsystem_device = selected_manager_params.get("subsystemSelect")
    subselect_device = subsystem_device.get("subsystemSelect")

    filtered_device = {
        key: value
        for key, value in subselect_device.items()
        if key not in ["name", "description", "type", "fitsname"] and value["value"]
    }

    return render(request, "devex/get_device.html", context={"filtered_device": filtered_device})


def get_state(request, manager):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    manager = "ScanCoordinator"
    selected_manager_params = get_params_for_manager(cc, manager)
    subsystem_state = selected_manager_params.get("subsystemState")
    subselect_state = subsystem_state.get("subsystemState")
    subselect_state_value = subselect_state.get("value")
    subselect_state_value = dict(zip(range(32), subselect_state_value, strict=True))
    filtered_state = {key: value
                      for key, value in subselect_state_value.items() if value != "NotInService"}

    return render(request, "devex/get_state.html", context={"filtered_state": filtered_state})


def get_status(request, manager):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    manager = "ScanCoordinator"
    selected_manager_params = get_params_for_manager(cc, manager)
    subsystem_status = selected_manager_params.get("subsystemStatus")
    subselect_status = subsystem_status.get("subsystemStatus")
    subselect_status_value = subselect_status.get("value")
    subselect_status_value = dict(zip(range(32), subselect_status_value, strict=True))
    subsystem_state = selected_manager_params.get("subsystemState")
    subselect_state = subsystem_state.get("subsystemState")
    subselect_state_value = subselect_state.get("value")
    subselect_state_value = dict(zip(range(32), subselect_state_value, strict=True))
    filtered_state = {key: value
                      for key, value in subselect_state_value.items() if value != "NotInService"}

    filtered_keys = set(filtered_state.keys())

    filtered_status = {
        key: value
        for key, value in subselect_status_value.items()
        if key in filtered_keys
    }

    return render(request, "devex/get_status.html", context={"filtered_status": filtered_status})

def get_antenna(request):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    manager3 = "Antenna.AntennaManager"
    selected_manager_samplers = get_samplers_for_manager(cc, manager3)
    azind = selected_manager_samplers.get("ccuData")
    azind2 = azind.get("ccuData")
    azind3 = azind2.get("AzEncoder")
    azind_indicated = azind3.get("indicated")
    azind_value = azind_indicated.get("value")

    azcom = selected_manager_samplers.get("ccuData")
    azcom2 = azcom.get("ccuData")
    azcom3 = azcom2.get("AzEncoder")
    azcom_commanded = azcom3.get("commanded")
    azcom_value = azcom_commanded.get("value")

    azrate = selected_manager_samplers.get("ccuData")
    azrate2 = azrate.get("ccuData")
    azrate3 = azrate2.get("AzEncoder")
    azrate_rate = azrate3.get("rate")
    azrate_value = azrate_rate.get("value")

    azerr = selected_manager_samplers.get("ccuData")
    azerr2 = azerr.get("ccuData")
    azerr3 = azerr2.get("AzEncoder")
    azerr_error = azerr3.get("error")
    azerr_value = azerr_error.get("value")

    elind = selected_manager_samplers.get("ccuData")
    elind2 = elind.get("ccuData")
    elind3 = elind2.get("ElEncoder")
    elind_indicated = elind3.get("indicated")
    elind_value = elind_indicated.get("value")

    elcom = selected_manager_samplers.get("ccuData")
    elcom2 = elcom.get("ccuData")
    elcom3 = elcom2.get("ElEncoder")
    elcom_commanded = elcom3.get("commanded")
    elcom_value = elcom_commanded.get("value")

    elrate = selected_manager_samplers.get("ccuData")
    elrate2 = elrate.get("ccuData")
    elrate3 = elrate2.get("ElEncoder")
    elrate_rate = elrate3.get("rate")
    elrate_value = elrate_rate.get("value")

    elerr = selected_manager_samplers.get("ccuData")
    elerr2 = elerr.get("ccuData")
    elerr3 = elerr2.get("ElEncoder")
    elerr_error = elerr3.get("error")
    elerr_value = elerr_error.get("value")

    return render(
        request,
        "devex/get_antenna.html",
        context={
            "azind_value":azind_value,
            "azcom_value":azcom_value,
            "azrate_value":azrate_value,
            "azerr_value":azerr_value,
            "elind_value":elind_value,
            "elcom_value":elcom_value,
            "elrate_value":elrate_value,
            "elerr_value":elerr_value,
        },
    )

def get_project(request):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)
    manager = "ScanCoordinator"
    selected_manager_params = get_params_for_manager(cc, manager)

    source = selected_manager_params.get("source")
    source_value = source.get("value")

    projectId = selected_manager_params.get("projectId")
    projectId2 = projectId.get("projectId")
    projectId_value = projectId2.get("value")

    start = selected_manager_params.get("startTime")
    start_field = start.get("startTime")
    start_field2 = start_field.get("seconds")
    start_value = start_field2.get("value")

    scannumber = selected_manager_params.get("scanNumber")
    scannumber2 = scannumber.get("scanNumber")
    scan_value = scannumber2.get("value")

    ssmaster = selected_manager_params.get("switching_signals_master")
    ssmaster2 = ssmaster.get("switching_signals_master")
    ssmaster_value = ssmaster2.get("value")

    length = selected_manager_params.get("scanLength")
    length_field = length.get("scanLength")
    length_field2 = length_field.get("seconds")
    length_value = length_field2.get("value")

    remain = selected_manager_params.get("scanRemaining")
    remain_field = remain.get("scanRemaining")
    remain_field2 = remain_field.get("seconds")
    remain_value = remain_field2.get("value")


    manager2 = "LO1"
    selected_manager_params2 = get_params_for_manager(cc, manager2)
    restFreq = selected_manager_params2.get("restFrequency")
    restFreq2 = restFreq.get("restFrequency")
    restFreq_value = restFreq2.get("value")

    restFrame = selected_manager_params2.get("restFrame")
    restFrame2 = restFrame.get("restFrame")
    restFrame_value = restFrame2.get("value")

    velocity = selected_manager_params2.get("sourceVelocity")
    getvelocity = velocity.get("sourceVelocity")
    velocity2 = getvelocity.get("theVelocity")
    velocitypos = velocity2.get("pos")
    velocity_value = velocitypos.get("value")

    veldef = selected_manager_params2.get("velocityDefinition")
    veldef2 = veldef.get("velocityDefinition")
    veldef_value = veldef2.get("value")

    return render(
        request,
        "devex/get_project.html",
        context={
            "source_value":source_value,
            "projectId_value":projectId_value,
            "start_value":start_value,
            "scan_value":scan_value,
            "ssmaster_value":ssmaster_value,
            "length_value":length_value,
            "remain_value":remain_value,
            "restFreq_value":restFreq_value,
            "restFrame_value":restFrame_value,
            "velocity_value":velocity_value,
            "veldef_value":veldef_value,
        },
    )


def status(request: HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    manager = "ScanCoordinator"

    selected_manager_params = get_params_for_manager(cc, manager)
    subsystem_state = selected_manager_params.get("subsystemState")
    subselect_state = subsystem_state.get("subsystemState")
    subselect_state_value = subselect_state.get("value")
    subselect_state_value = dict(zip(range(32), subselect_state_value, strict=True))
    filtered_state = {key: value
                      for key, value in subselect_state_value.items() if value != "NotInService"}

    filtered_keys = set(filtered_state.keys())


    subsystem_device = selected_manager_params.get("subsystemSelect")
    subselect_device = subsystem_device.get("subsystemSelect")


    filtered_device = {
        key: value
        for key, value in subselect_device.items()
        if key not in ["name", "description", "type", "fitsname"] and value["value"]
    }


    subsystem_status = selected_manager_params.get("subsystemStatus")
    subselect_status = subsystem_status.get("subsystemStatus")
    subselect_status_value = subselect_status.get("value")
    subselect_status_value = dict(zip(range(32), subselect_status_value, strict=True))

    filtered_status = {
        key: value
        for key, value in subselect_status_value.items()
        if key in filtered_keys
    }


# history log 
    history = History.objects.order_by("datetime").last()


# project info
    source = selected_manager_params.get("source")
    source_value = source.get("value")

    projectId = selected_manager_params.get("projectId")
    projectId2 = projectId.get("projectId")
    projectId_value = projectId2.get("value")

    start = selected_manager_params.get("startTime")
    start_field = start.get("startTime")
    start_field2 = start_field.get("seconds")
    start_value = start_field2.get("value")

    scannumber = selected_manager_params.get("scanNumber")
    scannumber2 = scannumber.get("scanNumber")
    scan_value = scannumber2.get("value")

    ssmaster = selected_manager_params.get("switching_signals_master")
    ssmaster2 = ssmaster.get("switching_signals_master")
    ssmaster_value = ssmaster2.get("value")

    length = selected_manager_params.get("scanLength")
    length_field = length.get("scanLength")
    length_field2 = length_field.get("seconds")
    length_value = length_field2.get("value")

    remain = selected_manager_params.get("scanRemaining")
    remain_field = remain.get("scanRemaining")
    remain_field2 = remain_field.get("seconds")
    remain_value = remain_field2.get("value")


    manager2 = "LO1"
    selected_manager_params2 = get_params_for_manager(cc, manager2)
    restFreq = selected_manager_params2.get("restFrequency")
    restFreq2 = restFreq.get("restFrequency")
    restFreq_value = restFreq2.get("value")

    restFrame = selected_manager_params2.get("restFrame")
    restFrame2 = restFrame.get("restFrame")
    restFrame_value = restFrame2.get("value")

    velocity = selected_manager_params2.get("sourceVelocity")
    getvelocity = velocity.get("sourceVelocity")
    velocity2 = getvelocity.get("theVelocity")
    velocitypos = velocity2.get("pos")
    velocity_value = velocitypos.get("value")

    veldef = selected_manager_params2.get("velocityDefinition")
    veldef2 = veldef.get("velocityDefinition")
    veldef_value = veldef2.get("value")

    # antenna info

    manager3 = "Antenna.AntennaManager"
    selected_manager_samplers = get_samplers_for_manager(cc, manager3)
    azind = selected_manager_samplers.get("ccuData")
    azind2 = azind.get("ccuData")
    azind3 = azind2.get("AzEncoder")
    azind_indicated = azind3.get("indicated")
    azind_value = azind_indicated.get("value")

    azcom = selected_manager_samplers.get("ccuData")
    azcom2 = azcom.get("ccuData")
    azcom3 = azcom2.get("AzEncoder")
    azcom_commanded = azcom3.get("commanded")
    azcom_value = azcom_commanded.get("value")

    azrate = selected_manager_samplers.get("ccuData")
    azrate2 = azrate.get("ccuData")
    azrate3 = azrate2.get("AzEncoder")
    azrate_rate = azrate3.get("rate")
    azrate_value = azrate_rate.get("value")

    azerr = selected_manager_samplers.get("ccuData")
    azerr2 = azerr.get("ccuData")
    azerr3 = azerr2.get("AzEncoder")
    azerr_error = azerr3.get("error")
    azerr_value = azerr_error.get("value")

    elind = selected_manager_samplers.get("ccuData")
    elind2 = elind.get("ccuData")
    elind3 = elind2.get("ElEncoder")
    elind_indicated = elind3.get("indicated")
    elind_value = elind_indicated.get("value")

    elcom = selected_manager_samplers.get("ccuData")
    elcom2 = elcom.get("ccuData")
    elcom3 = elcom2.get("ElEncoder")
    elcom_commanded = elcom3.get("commanded")
    elcom_value = elcom_commanded.get("value")

    elrate = selected_manager_samplers.get("ccuData")
    elrate2 = elrate.get("ccuData")
    elrate3 = elrate2.get("ElEncoder")
    elrate_rate = elrate3.get("rate")
    elrate_value = elrate_rate.get("value")

    elerr = selected_manager_samplers.get("ccuData")
    elerr2 = elerr.get("ccuData")
    elerr3 = elerr2.get("ElEncoder")
    elerr_error = elerr3.get("error")
    elerr_value = elerr_error.get("value")

    aldif = azcom_value - azind_value
    eldif = elcom_value - elind_value



    return render(
        request,
        "devex/status.html",
        context={
            "manager": manager,
            "selected_manager_params": selected_manager_params,
            "subsystem_device": subsystem_device,
            "subselect_device": subselect_device,
            "filtered_device": filtered_device,
            "subselect_status": subselect_status,
            "subselect_status_value": subselect_status_value,
            "filtered_status": filtered_status,
            "subselect_state": subselect_state,
            "subselect_state_value": subselect_state_value,
            "filtered_state": filtered_state,
            "filtered_keys": filtered_keys,
            "history": history,
            "source_value":source_value,
            "projectId_value":projectId_value,
            "start_value":start_value,
            "scan_value":scan_value,
            "ssmaster_value":ssmaster_value,
            "length_value":length_value,
            "remain_value":remain_value,
            "restFreq_value":restFreq_value,
            "restFrame_value":restFrame_value,
            "velocity_value":velocity_value,
            "veldef_value":veldef_value,
            "azind_value":azind_value,
            "azcom_value":azcom_value,
            "azrate_value":azrate_value,
            "azerr_value":azerr_value,
            "elind_value":elind_value,
            "elcom_value":elcom_value,
            "elrate_value":elrate_value,
            "elerr_value":elerr_value,
            "aldif":aldif,
            "eldif":eldif,



        },
    )


def home(request):
    return render(
            request,
            "devex/home.html")


def antenna(request:HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    manager3 = "Antenna.AntennaManager"
    selected_manager_samplers = get_samplers_for_manager(cc, manager3)
    azind = selected_manager_samplers.get("ccuData")
    azind2 = azind.get("ccuData")
    azind3 = azind2.get("AzEncoder")
    azind_indicated = azind3.get("indicated")
    azind_value = azind_indicated.get("value")

    azcom = selected_manager_samplers.get("ccuData")
    azcom2 = azcom.get("ccuData")
    azcom3 = azcom2.get("AzEncoder")
    azcom_commanded = azcom3.get("commanded")
    azcom_value = azcom_commanded.get("value")

    azrate = selected_manager_samplers.get("ccuData")
    azrate2 = azrate.get("ccuData")
    azrate3 = azrate2.get("AzEncoder")
    azrate_rate = azrate3.get("rate")
    azrate_value = azrate_rate.get("value")

    azerr = selected_manager_samplers.get("ccuData")
    azerr2 = azerr.get("ccuData")
    azerr3 = azerr2.get("AzEncoder")
    azerr_error = azerr3.get("error")
    azerr_value = azerr_error.get("value")

    elind = selected_manager_samplers.get("ccuData")
    elind2 = elind.get("ccuData")
    elind3 = elind2.get("ElEncoder")
    elind_indicated = elind3.get("indicated")
    elind_value = elind_indicated.get("value")

    elcom = selected_manager_samplers.get("ccuData")
    elcom2 = elcom.get("ccuData")
    elcom3 = elcom2.get("ElEncoder")
    elcom_commanded = elcom3.get("commanded")
    elcom_value = elcom_commanded.get("value")

    elrate = selected_manager_samplers.get("ccuData")
    elrate2 = elrate.get("ccuData")
    elrate3 = elrate2.get("ElEncoder")
    elrate_rate = elrate3.get("rate")
    elrate_value = elrate_rate.get("value")

    elerr = selected_manager_samplers.get("ccuData")
    elerr2 = elerr.get("ccuData")
    elerr3 = elerr2.get("ElEncoder")
    elerr_error = elerr3.get("error")
    elerr_value = elerr_error.get("value")

    raind = selected_manager_samplers.get("ccuData")
    raind2 = raind.get("ccuData")
    raind3 = raind2.get("RaJ2000")
    raind_indicated = raind3.get("indicated")
    raind_value = raind_indicated.get("value")

    return render(
        request,
        "devex/antenna.html",
        context={
            "azind_value":azind_value,
            "azcom_value":azcom_value,
            "azrate_value":azrate_value,
            "azerr_value":azerr_value,
            "elind_value":elind_value,
            "elcom_value":elcom_value,
            "elrate_value":elrate_value,
            "elerr_value":elerr_value,
            "raind_value":raind_value,
        },
    )