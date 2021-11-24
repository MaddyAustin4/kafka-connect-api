#  -*- coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2021 John Mille <john@compose-x.io>

"""Main module."""

import requests
from requests.auth import HTTPBasicAuth


class Task(object):
    """
    Class to represent a Connector Task
    """

    def __init__(self, api, connector, task_id, task_config):
        """

        :param Api api:
        :param Connector connector:
        :param int task_id:
        """
        self.task_id = task_id
        self._connector = connector
        self._api = api
        self.config = task_config

    @property
    def status(self):
        _query = self._api.get(
            f"/connectors/{self._connector.name}/tasks/{self.task_id}/status"
        )
        return _query

    def restart(self):
        _query = self._api.post(
            f"/connectors/{self._connector.name}/tasks/{self.task_id}/restart"
        )


class Connector(object):
    """
    Class to represent a Connector
    """

    def __init__(self, api, name, config=None):
        """

        :param Api api:
        :param str name:
        :param dict config:
        """
        self._api = api
        self.name = name
        if self.exists():
            self.config()

    def exists(self):
        req = self._api.get_raw(f"/connectors/{self.name}/")
        if req.status_code == 404:
            return False

    def restart(self):
        self._api.post(f"/connectors/{self.name}/restart")

    def pause(self):
        self._api.put(f"/connectors/{self.name}/pause")

    def resume(self):
        self._api.put(f"/connectors/{self.name}/resume")

    @property
    def config(self):
        _config = self._api.get(f"/connectors/{self.name}")
        return _config["config"]

    @config.setter
    def config(self, config):
        self._api.put(f"/connectors/{self.name}/config", data=config)

    @property
    def status(self):
        return self._api.get(f"/connectors/{self.name}/status")

    @property
    def tasks(self):
        _tasks = []
        _connector_tasks = self._api.get(f"/connectors/{self.name}/tasks")
        for _task in _connector_tasks:
            _tasks.append(
                Task(
                    self._api,
                    self,
                    task_id=int(_task["id"]["task"]),
                    task_config=_task["config"],
                )
            )
        return _tasks


class Cluster(object):
    def __init__(self, api):
        self._api = api

    def get(self):
        return self._api.get("/")

    @property
    def connectors(self):
        _connectors = self._api.get("/connectors")
        _cluster_connectors = {}
        for connector in _connectors:
            _cluster_connectors[connector] = Connector(self._api, connector)
        return _cluster_connectors


class Api(object):
    """
    Class to represent the Connect cluster
    """

    def __init__(
        self,
        hostname,
        port=None,
        protocol=None,
        ignore_ssl_errors=False,
        username=None,
        password=None,
    ):
        """

        :param str hostname:
        :param int port:
        :param str protocol:
        :param bool ignore_ssl_errors:
        :param str username:
        :param str password:
        """
        self.hostname = hostname
        self.protocol = protocol if protocol else "http"
        self.ignore_ssl = ignore_ssl_errors
        self.port = port if port else 8083
        self.username = username
        self.password = password

        if self.protocol not in ["http", "https"]:
            raise ValueError("protocol must be one of", ["http", "https"])
        if (self.port < 0) or (self.port > (2 ** 16)):
            raise ValueError(
                f"Port {self.port} is not valid. Must be between 0 and {((2 ** 16) - 1)}"
            )
        if self.username and not self.password or self.password and not self.username:
            raise ValueError("You must specify both username and password")

        if (self.port == 80 and protocol == "http") or (
            self.port == 443 and self.protocol == "https"
        ):
            self.url = f"{self.protocol}://{self.hostname}"
        else:
            self.url = f"{self.protocol}://{self.hostname}:{self.port}"

        self.auth = (
            HTTPBasicAuth(self.username, self.password)
            if self.username and self.password
            else None
        )

        self.headers = {
            "Content-type": "content_type_value",
            "Accept": "application/json",
        }

    def get_raw(self, query_path):
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = requests.get(url, auth=self.auth, headers=self.headers)
        return req

    def get(self, query_path):
        req = self.get_raw(query_path)
        return req.json()

    def post_raw(self, query_path, data=None):
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = requests.post(url, auth=self.auth, headers=self.headers, data=data)
        return req

    def post(self, query_path, data=None):
        req = self.post_raw(query_path, data)
        return req.json()

    def put_raw(self, query_path, data=None):
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = requests.put(url, auth=self.auth, headers=self.headers, data=data)
        return req

    def put(self, query_path, data=None):
        req = self.put_raw(query_path, data)
        return req.json()

    def delete_raw(self, query_path):
        if not query_path.startswith(r"/"):
            query_path = f"/{query_path}"
        url = f"{self.url}{query_path}"
        req = requests.delete(url, auth=self.auth, headers=self.headers)
        return req

    def delete(self, query_path):
        req = self.delete_raw(query_path)
        return req.json()
