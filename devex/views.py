from typing import Any
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from zmqgc import ZMQGrailClient as ChaliceClient
from tortoise.models import History, ObsProcedure, ObsProjectRef, Observer, Operator
from django.views import generic
from django.conf import settings
from alda.atoll.models import Article, ArticleRef, ArticleType, AstridScript, ExecutedAstridScript, McDevice, McHost, McMessage, McMessageTemplate, MetaProject, Person
from alda.audit.models import FileHost, FileImportAttempt, FileImporter
from alda.disk.models import DataProduct, DataProductType, DataTransfer, DataTransferGroup, FitsFile, FitsHeader, Manager, ManagerFolder, Problem, Project, Scan, ScanLog, ScanLogFile, ScanLogManagerFolder, ScanLogScan, SessionExport, SessionFile, SessionImport, SessionPart, SessionPartExport, SessionPartImport, Stats
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
from collections import namedtuple
import math
from io import BytesIO
from matplotlib.animation import FuncAnimation
import astropy.coordinates as coord
import astropy.units as u
from astropy import units as u
from astropy.coordinates import Angle
import xml.etree.ElementTree as ET
import io, base64



def info(request):
    histories = History.objects.order_by("-datetime")[:15]

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

def get_script (request):
    histories = History.objects.order_by("-datetime")[:15]

    return render(
            request,
            "devex/get_script.html",
            context={
                "histories": histories,
            }
        )

def get_script_status(request):
    history = History.objects.order_by("datetime").last()
    return render(
            request,
            "devex/get_script_status.html",
            context={
                "history": history,
            },
        )

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


    try:
        subselect_state_value = dict(zip(range(35), subselect_state_value))
    except ValueError:
        subselect_state_value = {}

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

    subsystem_state = selected_manager_params.get("subsystemState")
    subselect_state = subsystem_state.get("subsystemState")
    subselect_state_value = subselect_state.get("value")


    try:
        subselect_state_value = dict(zip(range(35), subselect_state_value))
    except ValueError:
        subselect_state_value = {}

    filtered_state = {key: value
                    for key, value in subselect_state_value.items() if value != "NotInService"}
    

    filtered_keys = set(filtered_state.keys())


    try:
        subselect_status_value = dict(zip(range(35), subselect_status_value))
    except ValueError:
        subselect_status_value = {}

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

    color1 = 'b'
    label1 = 'Indicated'
    color2 = 'r'
    label2 = 'Commanded'
    svg_image = init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)

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
            "svg_image":svg_image,
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

    try:
        subselect_state_value = dict(zip(range(35), subselect_state_value))
    except ValueError:
        subselect_state_value = {}

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

    try:
        subselect_status_value = dict(zip(range(35), subselect_status_value))
    except ValueError:
        subselect_status_value = {}

    filtered_status = {
        key: value
        for key, value in subselect_status_value.items()
        if key in filtered_keys
    }


# history log 
    history = History.objects.order_by("datetime").last()

#CLEO messages
    message = McMessage.objects.order_by("-sort_time")[:2]


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


    color1 = 'b'
    label1 = 'Indicated'
    color2 = 'r'
    label2 = 'Commanded'
    svg_image = init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)

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
            "message": message,
            "svg_image":svg_image,



        },
    )


def home(request):
    return render(
            request,
            "devex/home.html")


def messages(request):
    messages = McMessage.objects.order_by("-sort_time")[:10]

    return render(
                request,
                "devex/messages.html",
                context={
                    "messages": messages,
                }
            )

def get_messages(request):
    messages = McMessage.objects.order_by("-sort_time")[:10]

    return render(
                request,
                "devex/get_messages.html",
                context={
                    "messages": messages,
                }
            )

def get_messages_main(request):
    message = McMessage.objects.order_by("-sort_time")[:2]

    return render(
                request,
                "devex/get_messages_main.html",
                context={
                    "message": message,
                }
            )



#antenna plotting code

Coordinates = namedtuple("Coordinates", ["x", "y"])

def format_y_axis(x, pos):
    return f"{x*90:.0f}°"

def init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2):

    #convert degrees to radians for azimuth values
    azind_value = math.radians(azind_value)
    azcom_value = math.radians(azcom_value)

    # normalize elevation to fit radial distance
    elind_value = elind_value / 90
    elcom_value = elcom_value / 90

    fig = plt.figure(figsize=(6, 8))
    ax = fig.add_subplot(polar=True)
    ax.plot(azind_value, elind_value, marker='o', linestyle='None', color=color1, label=label1)
    ax.plot(azcom_value, elcom_value, marker='x', linestyle='None', color=color2, label=label2)
    ax.xaxis.grid(True, color="grey", alpha=0.6)
    ax.yaxis.grid(True, color="grey", alpha=0.6)
    ax.set_rlabel_position(90 + 22.5)
    ax.set_rlim(bottom=0, top=1)
    ax.set_rticks([0, 30/90, 60/90, 90/90])  # r-ticks in normalized values
    ax.set_theta_zero_location("N")
    ax.grid(True)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(format_y_axis))
    ax.set_title('Antenna Position', pad=15)
    plt.tight_layout()
    ax.legend(loc='upper left', bbox_to_anchor=(0, 1.1))

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    # ax_table = fig.add_subplot()
    # ax_table.axis('off')

    # indicated_az = round(math.degrees(azind_value),5)
    # commanded_az = round(math.degrees(azcom_value),5)
    # indicated_el = round(elind_value * 90,5)
    # commanded_el = round(elcom_value * 90,5)

    # table
    # data = {'': [label1, label2],
    #         'Azimuth': [f"{indicated_az}°", f"{commanded_az}°"],
    #         'Elevation': [f"{indicated_el}°", f"{commanded_el}°"] 
    # }

    # df = pd.DataFrame(data)
    # table = ax_table.table(cellText=df.values, colLabels=df.columns, cellLoc='center')
    # table.auto_set_font_size(False)
    # table.set_fontsize(10)
    # table.scale(1, 1.5)
    fig.tight_layout()


    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)

    # Encode the image to base64
    return base64.b64encode(buf.getvalue()).decode()




def init_plot_J2000(raind_value, dcind_value, racom_value, dccom_value):
    RA_indicated_deg = raind_value
    RA_commanded_deg = racom_value

    Dec_indicated_deg = dcind_value
    Dec_commanded_deg = dccom_value
    ra_indicated = Angle(RA_indicated_deg * u.degree)
    ra_commanded = Angle(RA_commanded_deg * u.degree)

    # ra_ind_hours = ra_indicated.to_string(unit=u.hour, precision=2, pad=True)
    # ra_com_hours = ra_commanded.to_string(unit=u.hour, precision=2, pad=True)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="mollweide")

    ax.scatter(ra_indicated.radian, Dec_indicated_deg * u.degree, marker='o', color='blue', label='Indicated')
    ax.scatter(ra_commanded.radian, Dec_commanded_deg * u.degree, marker='x', color='red', label='Commanded')

    ax.set_xticklabels(['10h', '8h', '6h', '4h', '2h', '0h', '22h', '20h','18h','16h','14h',])
    ax.grid(True)
    ax.legend(loc='upper right')
    plt.title('ICRS Position', pad=15)
    plt.xlabel('RA [hours]')
    plt.ylabel('Dec [degrees]')


    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    # ax_table = fig.add_subplot()
    # ax_table.axis('off')
    # data = {
    #     '': ['Indicated', 'Commanded'],
    #     'RA': [ra_ind_hours, ra_com_hours],
    #     'Dec': [f'{dcind_value:.2f}°', f'{dccom_value:.2f}°']
    # }


    # df = pd.DataFrame(data)

    # table = ax_table.table(cellText=df.values, colLabels=df.columns, cellLoc='center')
    # table.auto_set_font_size(False)
    # table.set_fontsize(10)
    # table.scale(1, 1.5) 

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)

    # Encode the image to base64
    return base64.b64encode(buf.getvalue()).decode()




def init_plot_galactic(loind_value, laind_value, lacom_value, locom_value):

    LO_indicated_deg = loind_value
    LO_commanded_deg = locom_value

    LA_indicated_deg = laind_value
    LA_commanded_deg = lacom_value

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="mollweide")

    ax.scatter(coord.Angle(LO_indicated_deg * u.degree).wrap_at(180*u.degree).radian,
            coord.Angle(LA_indicated_deg * u.degree).radian,
            marker='o', color='blue', label='Indicated')

    ax.scatter(coord.Angle(LO_commanded_deg * u.degree).wrap_at(180*u.degree).radian,
            coord.Angle(LA_commanded_deg * u.degree).radian,
            marker='x', color='red', label='Commanded')

    ax.grid(True)
    ax.legend(loc='upper right')

    plt.title('Galactic Position', pad=15)
    plt.xlabel('Longitude [degrees]')
    plt.ylabel('Latitude [degrees]')

    ra_ticks = [210, 240, 270, 300, 330, 0, 30, 60, 90, 120, 150]
    ra_ticks_wrapped = [tick if tick <= 180 else tick - 360 for tick in ra_ticks]
    ra_labels = [f'{tick}°' for tick in ra_ticks]

    ax.set_xticks([tick * u.degree.to(u.radian) for tick in ra_ticks_wrapped])
    ax.set_xticklabels(ra_labels)

    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)

    #table
    # ax_table = fig.add_subplot()
    # ax_table.axis('off')

    # data = {
    #     '': ['Indicated', 'Commanded'],
    #     'Longitude': [f'{LO_indicated_deg:.2f}°', f'{LO_commanded_deg:.2f}°'],
    #     'Latitude': [f'{LA_indicated_deg:.2f}°', f'{LA_commanded_deg:.2f}°']
    # }

    # df = pd.DataFrame(data)

    # table = ax_table.table(cellText=df.values, colLabels=df.columns, cellLoc='center')
    # table.auto_set_font_size(False)
    # table.set_fontsize(10)
    # table.scale(1, 1.5)

    fig.tight_layout()

    # Save the figure to a BytesIO buffer as PNG
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)

    # Encode the image to base64
    return base64.b64encode(buf.getvalue()).decode()






def antenna(request:HttpRequest):
    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    manager3 = "Antenna.AntennaManager"
    selected_manager_samplers = get_samplers_for_manager(cc, manager3)

#Azimuth Values (indicated, commanded, rate, error)  
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

#Elevation Values (indicated, commanded, rate, error)
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

#Right Ascension Values (indicated, commanded, rate)
    raind = selected_manager_samplers.get("ccuData")
    raind2 = raind.get("ccuData")
    raind3 = raind2.get("RaJ2000")
    raind_indicated = raind3.get("indicated")
    raind_value = raind_indicated.get("value")

    racom = selected_manager_samplers.get("ccuData")
    racom2 = racom.get("ccuData")
    racom3 = racom2.get("RaJ2000")
    racom_indicated = racom3.get("commanded")
    racom_value = racom_indicated.get("value")

    rarate = selected_manager_samplers.get("ccuData")
    rarate2 = rarate.get("ccuData")
    rarate3 = rarate2.get("RaJ2000")
    rarate_indicated = rarate3.get("rate")
    rarate_value = rarate_indicated.get("value")

#Declination Values (indicated, commanded, rate)
    dcind = selected_manager_samplers.get("ccuData")
    dcind2 = dcind.get("ccuData")
    dcind3 = dcind2.get("DcJ2000")
    dcind_indicated = dcind3.get("indicated")
    dcind_value = dcind_indicated.get("value")

    dccom = selected_manager_samplers.get("ccuData")
    dccom2 = dccom.get("ccuData")
    dccom3 = dccom2.get("DcJ2000")
    dccom_indicated = dccom3.get("indicated")
    dccom_value = dccom_indicated.get("value")

    dcrate = selected_manager_samplers.get("ccuData")
    dcrate2 = dcrate.get("ccuData")
    dcrate3 = dcrate2.get("DcJ2000")
    dcrate_indicated = dcrate3.get("indicated")
    dcrate_value = dcrate_indicated.get("value")

#Longitude Values (indicated, commanded, rate)
    loind = selected_manager_samplers.get("ccuData")
    loind2 = loind.get("ccuData")
    loind3 = loind2.get("Gal_L")
    loind_indicated = loind3.get("indicated")
    loind_value = loind_indicated.get("value")

    locom = selected_manager_samplers.get("ccuData")
    locom2 = locom.get("ccuData")
    locom3 = locom2.get("Gal_L")
    locom_commanded = locom3.get("commanded")
    locom_value = locom_commanded.get("value")

    lorate = selected_manager_samplers.get("ccuData")
    lorate2 = lorate.get("ccuData")
    lorate3 = lorate2.get("Gal_L")
    lorate_rate = lorate3.get("rate")
    lorate_value = lorate_rate.get("value")

#Latitude Values (indicated, commanded, rate)
    laind = selected_manager_samplers.get("ccuData")
    laind2 = laind.get("ccuData")
    laind3 = laind2.get("Gal_B")
    laind_indicated = laind3.get("indicated")
    laind_value = laind_indicated.get("value")

    lacom = selected_manager_samplers.get("ccuData")
    lacom2 = lacom.get("ccuData")
    lacom3 = lacom2.get("Gal_B")
    lacom_commanded = lacom3.get("commanded")
    lacom_value = lacom_commanded.get("value")

    larate = selected_manager_samplers.get("ccuData")
    larate2 = larate.get("ccuData")
    larate3 = larate2.get("Gal_B")
    larate_rate = larate3.get("rate")
    larate_value = larate_rate.get("value")

    color1 = 'b'
    label1 = 'Indicated'
    color2 = 'r'
    label2 = 'Commanded'
    svg_image = init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)

    svg_image_J2000 = init_plot_J2000(raind_value, dcind_value, racom_value, dccom_value)

    svg_image_galactic = init_plot_galactic(loind_value, laind_value, lacom_value, locom_value)

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
            "dcind_value":dcind_value,
            "racom_value":racom_value,
            "rarate_value":rarate_value,
            "dccom_value":dccom_value,
            "dcrate_value":dcrate_value,
            "loind_value":loind_value,
            "locom_value":locom_value,
            "lorate_value":lorate_value,
            "laind_value":laind_value,
            "lacom_value":lacom_value,
            "larate_value":larate_value,
            "svg_image":svg_image,
            "svg_image_J2000":svg_image_J2000,
            "svg_image_galactic":svg_image_galactic,

        },
    )


def get_antenna_main(request:HttpRequest):

    cc = ChaliceClient(host=settings.CHALICE_HOST, port=settings.CHALICE_PORT)

    manager3 = "Antenna.AntennaManager"
    selected_manager_samplers = get_samplers_for_manager(cc, manager3)

#Azimuth Values (indicated, commanded, rate, error)  
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

#Elevation Values (indicated, commanded, rate, error)
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

#Right Ascension Values (indicated, commanded, rate)
    raind = selected_manager_samplers.get("ccuData")
    raind2 = raind.get("ccuData")
    raind3 = raind2.get("RaJ2000")
    raind_indicated = raind3.get("indicated")
    raind_value = raind_indicated.get("value")

    racom = selected_manager_samplers.get("ccuData")
    racom2 = racom.get("ccuData")
    racom3 = racom2.get("RaJ2000")
    racom_indicated = racom3.get("commanded")
    racom_value = racom_indicated.get("value")

    rarate = selected_manager_samplers.get("ccuData")
    rarate2 = rarate.get("ccuData")
    rarate3 = rarate2.get("RaJ2000")
    rarate_indicated = rarate3.get("rate")
    rarate_value = rarate_indicated.get("value")

#Declination Values (indicated, commanded, rate)
    dcind = selected_manager_samplers.get("ccuData")
    dcind2 = dcind.get("ccuData")
    dcind3 = dcind2.get("DcJ2000")
    dcind_indicated = dcind3.get("indicated")
    dcind_value = dcind_indicated.get("value")

    dccom = selected_manager_samplers.get("ccuData")
    dccom2 = dccom.get("ccuData")
    dccom3 = dccom2.get("DcJ2000")
    dccom_indicated = dccom3.get("indicated")
    dccom_value = dccom_indicated.get("value")

    dcrate = selected_manager_samplers.get("ccuData")
    dcrate2 = dcrate.get("ccuData")
    dcrate3 = dcrate2.get("DcJ2000")
    dcrate_indicated = dcrate3.get("indicated")
    dcrate_value = dcrate_indicated.get("value")

#Longitude Values (indicated, commanded, rate)
    loind = selected_manager_samplers.get("ccuData")
    loind2 = loind.get("ccuData")
    loind3 = loind2.get("Gal_L")
    loind_indicated = loind3.get("indicated")
    loind_value = loind_indicated.get("value")

    locom = selected_manager_samplers.get("ccuData")
    locom2 = locom.get("ccuData")
    locom3 = locom2.get("Gal_L")
    locom_commanded = locom3.get("commanded")
    locom_value = locom_commanded.get("value")

    lorate = selected_manager_samplers.get("ccuData")
    lorate2 = lorate.get("ccuData")
    lorate3 = lorate2.get("Gal_L")
    lorate_rate = lorate3.get("rate")
    lorate_value = lorate_rate.get("value")

#Latitude Values (indicated, commanded, rate)
    laind = selected_manager_samplers.get("ccuData")
    laind2 = laind.get("ccuData")
    laind3 = laind2.get("Gal_B")
    laind_indicated = laind3.get("indicated")
    laind_value = laind_indicated.get("value")

    lacom = selected_manager_samplers.get("ccuData")
    lacom2 = lacom.get("ccuData")
    lacom3 = lacom2.get("Gal_B")
    lacom_commanded = lacom3.get("commanded")
    lacom_value = lacom_commanded.get("value")

    larate = selected_manager_samplers.get("ccuData")
    larate2 = larate.get("ccuData")
    larate3 = larate2.get("Gal_B")
    larate_rate = larate3.get("rate")
    larate_value = larate_rate.get("value")

    color1 = 'b'
    label1 = 'Indicated'
    color2 = 'r'
    label2 = 'Commanded'

    svg_image = init_plot(azind_value, elind_value, color1, label1, azcom_value, elcom_value, color2, label2)

    svg_image_J2000 = init_plot_J2000(raind_value, dcind_value, racom_value, dccom_value)

    svg_image_galactic = init_plot_galactic(loind_value, laind_value, lacom_value, locom_value)


    return render(
        request,
        "devex/get_antenna_main.html",
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
            "dcind_value":dcind_value,
            "racom_value":racom_value,
            "rarate_value":rarate_value,
            "dccom_value":dccom_value,
            "dcrate_value":dcrate_value,
            "loind_value":loind_value,
            "locom_value":locom_value,
            "lorate_value":lorate_value,
            "laind_value":laind_value,
            "lacom_value":lacom_value,
            "larate_value":larate_value,
            "svg_image":svg_image,
            "svg_image_J2000":svg_image_J2000,
            "svg_image_galactic":svg_image_galactic,

        },
    )

