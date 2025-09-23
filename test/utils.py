import socket

import requests
from client import worker


def execute_gpao_client(tags: str = "docker", num_thread: int = 1):
    """Execute a GPAO client on this host"""
    parameters = {
        "url_api": worker.GPAO_API_URL,
        "hostname": socket.gethostname(),
        "tags": tags,
        "autostart": "2",
        "mode_exec_and_quit": True,
        "suffix": "",
    }
    worker.exec_multiprocess(num_thread, parameters)


def delete_projects_starting_with(project_name: str):
    """Delete all projects that have this name"""
    response = worker.send_request(worker.GPAO_API_URL + "projects", "GET")
    id_list = []
    if response and response.json():
        for proj in response.json():
            if proj["project_name"].startswith(project_name):
                proj_id = proj["project_id"]
                id_list.append(proj_id)
    json_ids = {"ids": id_list}
    response = requests.delete(worker.GPAO_API_URL + "projects/delete", json=json_ids)
