from tempfile import TemporaryFile
from typing import List, Any
import numpy as np
import requests
import tarfile
import time

from kubernetes.client.rest import ApiException
from kubernetes.client import (
    V1ResourceRequirements,
    CustomObjectsApi,
    V1ObjectMeta,
    V1Container,
    V1Namespace,
    V1PodSpec,
    CoreV1Api,
    V1Pod,
    V1Node,
    V1Service,
    V1ServiceSpec,
    V1ServicePort
)
from kubernetes import config, stream

from utils import generate_random_str, get_pod_name, get_service_name
import logger


class BaseFunctionalities:
    """Base Class of Funtionalities"""

    NAMESPACE_ACTIVE = 'Active'
    POD_RUNNING = 'Running'

    def __init__(
            self,
            API: CoreV1Api,
            ObjectAPI: CustomObjectsApi,
            namespace: str,
    ):
        """BaseFunctionalities Constructor

        :param API: CoreV1Api
            get API of kubernetes for accessing by general api

        :param ObjectAPI: CustomObjectsApi
            get API of kubernetes for accessing by object

        :param namespace: str
            name of used namespace
        """

        # CoreV1Api interface
        self._api: CoreV1Api = API

        # CustomObjectApi interface
        self._object_api: CustomObjectsApi = ObjectAPI

        # Define using namespace
        self.namespace: str = namespace

    def _check_namespace(self, namespace: str):
        """Check namespace

        if namespace does not exist, it will be create.

        :param namespace: str
            name of namespace
        """
        try:
            ns = self._api.read_namespace(namespace)
            return ns
        except ApiException as e:
            logger.warn("namespace '{}' does not exist, so it will be created.".format(
                namespace
            ))

        logger.info("Creating Namespace '{}'".format(
            namespace
        ))

        try:
            self._api.create_namespace(V1Namespace(metadata=V1ObjectMeta(name=namespace)))
        except ApiException as e:
            logger.error(e)

        logger.info('Waiting for creating namespace "{}"'.format(
            namespace
        ))

        while True:
            time.sleep(1)
            try:
                ns = self._api.read_namespace(namespace)
                if ns.status.phase == self.NAMESPACE_ACTIVE:
                    logger.info("namespace '{}' created successfully".format(
                        namespace
                    ))
                    return ns
            except ApiException as e:
                logger.warn("namespace '{}' does not exist, so it will be created.".format(
                    namespace
                ))


class Monitor(BaseFunctionalities):
    """Monitoring Functionalities

        Monitoring a kubernetes cluster
    """

    def __init__(
            self,
            API: CoreV1Api,
            ObjectAPI: CustomObjectsApi,
            namespace: str,
    ):
        """Monitor Constructor

        :param API: CoreV1Api
            get API of kubernetes for accessing by general api

        :param ObjectAPI: CustomObjectsApi
            get API of kubernetes for accessing by object

        :param namespace: str
            name of used namespace
        """
        super().__init__(API, ObjectAPI, namespace)

    def get_nodes(self) -> (List[V1Node], V1Node):
        """Get Nodes"""

        # get all computational nodes
        nodes = [
            node for node in sorted(self._api.list_node().items, key=lambda node: node.metadata.name)
            if 'master' not in node.metadata.name
        ]

        try:
            return nodes
        except ApiException as e:
            logger.error(e)

        return None

    def get_pod(self, name: str, namespace: str = None):
        """Get specific Pod

        :param name: str
            name of pod

        :param namespace: str
            namespace of pod
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            return self._api.read_namespaced_pod(name, namespace)
        except ApiException as e:
            logger.error(e)
        return None

    def get_pods(self, namespace: str = None):
        """Get Pods

        :param namespace: str
            get pods of a specific namespace
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            return self._api.list_namespaced_pod(namespace).items
        except ApiException as e:
            logger.error(e)
        return None

    def get_pods_metrics(self, namespace: str = None):
        """Get Pod Metrics

        :param namespace: str
            get pod metrics of a specific namespace
        """

        def containers(metrics):
            items = metrics.get('items')
            conts = {
                item.get('metadata').get('name'):
                    item.get('containers')[0].get('usage')
                for item in items if len(item.get('containers')) > 0
            }
            return conts

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            while True:
                metrics = self._object_api \
                    .list_namespaced_custom_object('metrics.k8s.io', 'v1beta1', namespace, 'pods')

                if len(metrics.get('items')) > 0:
                    return containers(metrics)

                time.sleep(1)

        except ApiException as e:
            logger.error(e)
        return None

    def get_pod_metrics(self, pod_name: str, namespace: str = None):
        """Get Pod Metrics

        :param pod_name: str
            name of pod

        :param namespace: str
            get pod metrics of a specific namespace
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            return self._object_api \
                .get_namespaced_custom_object('metrics.k8s.io', 'v1beta1', namespace, 'pods', pod_name) \
                .get('containers') \
                .pop() \
                .get('usage')
        except ApiException as e:
            logger.error(e)
        return None

    def get_nodes_metrics(self):
        """Get Nodes Metrics"""

        def metrics(nodes):
            return {
                node.get('metadata').get('name'): node.get('usage')
                for node in nodes
            }

        try:
            return metrics(self._object_api \
                           .list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes') \
                           .get('items'))
        except ApiException as e:
            logger.error(e)
        return None

    def get_node_metrics(self, node_name: str):
        """Get Node Metrics

        :param node_name: str
            name of node
        """
        try:
            return self._object_api \
                .get_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes', node_name) \
                .get('usage')
        except ApiException as e:
            logger.error(e)
        return None


class Action(BaseFunctionalities):
    """Kubernetes Cluster - Actions"""

    UTILIZATION_NODE_PORT = 30000

    DATA_DESTINATION = "/"
    WORKLOAD_NAME = 'workloads.pickle'

    def __init__(
            self,
            API: CoreV1Api,
            ObjectAPI: CustomObjectsApi,
            namespace: str,
            workloads_path: str,
            utilization_server_image: str,
            node: V1Node,
            cleaning_after_exiting: bool = False,
    ):
        """Actions Constructor

        :param API: CoreV1Api
            get API of kubernetes for accessing by general api

        :param ObjectAPI: CustomObjectsApi
            get API of kubernetes for accessing by object

        :param namespace: str
            name of used namespace

        :param workloads_path: str
            path of workloads

        :param utilization_server_image: str
            using this image for utilization server

        :param cleaning_after_exiting: bool (default: False)
            clean the cluster after exiting
        """
        super().__init__(API, ObjectAPI, namespace)

        # this variable will be used to get external IP for connecting to the utilization-server
        self.node: V1Node = node

        self.cleaning_after_exiting: bool = cleaning_after_exiting

        self.utilization_server_image: str = utilization_server_image

        self.workloads_path: str = workloads_path

        if self.cleaning_after_exiting:
            self._setup_signal()

        # setup utilization server
        self._setup_utilization_server(image=self.utilization_server_image)

    def _setup_signal(self):
        """Setting Up signals"""
        logger.info('setting up signal handlers...')
        import signal
        signal.signal(signal.SIGTERM, self._exiting)
        signal.signal(signal.SIGINT, self._exiting)

    def _exiting(self, signum, frame):
        """Exiting function
            It will be triggered after catch the kill or terminate signals
            , and clean the cluster
        """
        logger.info('clean the cluster in exiting...')
        self.clean()
        exit(0)

    def _setup_utilization_server(self, image: str):
        """Setup Utilization Server

        :param image: str
            using this image to start the utilization server
        """

        # firstly clean the cluster
        self.clean(self.namespace)

        name = "utilization-server"

        # create a container
        pod = V1Pod(
            api_version='v1',
            kind='Pod',
            metadata=V1ObjectMeta(
                name=name,
                labels=dict(
                    env='Park',
                    type=name
                ),
                namespace=self.namespace
            ),
            spec=V1PodSpec(
                hostname=name,
                containers=[
                    V1Container(
                        name=name,
                        image=image,
                        # image_pull_policy='IfNotPresent'
                    )
                ]
            )
        )

        logger.info("Creating pod '{}' ...".format(name))
        if self.create_pod(pod) is None:
            logger.error("can't create pod '{}', so we will exit.. ".format(name))
            self.clean(self.namespace)
            exit(1)

        # create a service
        service = V1Service(
            api_version="v1",
            kind="Service",
            metadata=V1ObjectMeta(
                name=name,
                labels=dict(
                    env='Park',
                    type=name
                ),
                namespace=self.namespace
            ),
            spec=V1ServiceSpec(
                ports=[
                    V1ServicePort(
                        name="web", protocol="TCP", port=80, target_port=80, node_port=self.UTILIZATION_NODE_PORT
                    )
                ],
                type='NodePort',
                selector=dict(
                    type=name
                )
            )
        )
        logger.info("Creating service '{}' ... ".format(name))
        if self.create_service(service) is None:
            logger.error("can't create service '{}', so we will exit.. ".format(name))
            self.clean(self.namespace)
            exit(1)

        # upload workload file into container
        self.copy_file_inside_pod(
            pod_name=name,
            arcname=self.WORKLOAD_NAME,
            src_path=self.workloads_path,
            dest_path=self.DATA_DESTINATION,
            namespace=self.namespace
        )

    def copy_file_inside_pod(self, pod_name: str, arcname: str, src_path: str, dest_path: str, namespace=None):
        """This function copies a file inside the pod
        :param pod_name: pod name
        :param arcname: actual name of file
        :param src_path: Source path of the file to be copied from
        :param dest_path: Destination path of the file to be copied into
        :param namespace: pod namespace
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            exec_command = ['tar', 'xvf', '-', '-C', dest_path]
            api_response = stream.stream(
                self._api.connect_get_namespaced_pod_exec, pod_name, namespace,
                command=exec_command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False
            )

            logger.info('Uploading file "{}" to "{}" ...'.format(
                src_path, pod_name
            ))
            with TemporaryFile() as tar_buffer:
                with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                    tar.add(name=src_path, arcname=arcname)

                tar_buffer.seek(0)
                commands = [tar_buffer.read()]
                while api_response.is_open():
                    api_response.update(timeout=10)
                    if api_response.peek_stdout():
                        logger.info("uploading file %s successful." % api_response.read_stdout())
                    if api_response.peek_stderr():
                        logger.error("uploading file %s failed." % api_response.read_stderr())
                    if commands:
                        c = commands.pop(0)
                        api_response.write_stdin(c)
                    else:
                        break
                api_response.close()
        except ApiException as e:
            logger.error("Exception when copying file to the pod: {}".format(e))
            self.clean(self.namespace)
            exit(1)

    def create_pods(self, pods: List[V1Pod], namespace: str = None):
        """Create multiple Pods

        :param pods: List[V1Pod]
            a list of pods for creation

        :param namespace: str
            namespace of Pods
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        # create all pods
        _pods = [self.create_pod(pod, namespace) for pod in pods]

        # check all pods created or not
        if None in _pods:
            raise Exception('pods did not create.')

        return _pods

    def create_pod(self, pod: V1Pod, namespace: str = None):
        """Create a Pod

        :param pod: V1Pod
            pod object

        :param namespace: str
            namespace of Pod
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        # check namespace
        self._check_namespace(namespace)

        try:
            self._api.create_namespaced_pod(namespace, pod)

            logger.info('Waiting for Pod "{}" to run ...'.format(
                get_pod_name(pod)
            ))

            while True:
                time.sleep(1)
                pod = self._api.read_namespaced_pod(pod.metadata.name, namespace)
                if pod.status.phase == self.POD_RUNNING:
                    logger.info('Pod "{}" is Running'.format(
                        get_pod_name(pod)
                    ))
                    return pod
        except ApiException as e:
            logger.error(e)
        return None

    def create_service(self, service: V1Service, namespace: str = None):
        """Create a Service

        :param service: V1Service
            pod object

        :param namespace: str
            namespace of service
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        # check namespace
        self._check_namespace(namespace)

        try:
            logger.info('Waiting for Service "{}" to run ...'.format(
                get_service_name(service)
            ))
            return self._api.create_namespaced_service(namespace, service)
        except ApiException as e:
            logger.error(e)
        return None

    def create_services(self, services: List[V1Service], namespace: str = None):
        """Create multiple Services

        :param services: List[V1Services]
            a list of services for creation

        :param namespace: str
            namespace of services
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        # create all pods
        _services = [self.create_service(service, namespace) for service in services]

        # check all pods created or not
        if None in _services:
            raise Exception('services did not create.')

        return _services

    def delete_pod(self, name: str, namespace: str = None):
        """Delete a specific Pod

        :param name: str
            name of Pod

        :param namespace: str
            namespace of Pod
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            self._api.delete_namespaced_pod(name, namespace)
        except ApiException as e:
            logger.error(e)

        try:
            while True:
                self._api.read_namespaced_pod(name, namespace)
                time.sleep(1)
        except ApiException as e:
            logger.info('Pod "{}" deleted.'.format(name))

        return True

    def delete_service(self, name: str, namespace: str = None):
        """Delete a specific Service

        :param name: str
            name of Service

        :param namespace: str
            namespace of Service
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            self._api.delete_namespaced_service(name, namespace)
        except ApiException as e:
            logger.error(e)

        try:
            while True:
                self._api.read_namespaced_service(name, namespace)
                time.sleep(1)
        except ApiException as e:
            logger.info('Service "{}" deleted.'.format(name))

        return True

    def move_pod(
            self,
            previousPod: V1Pod,
            previousService: V1Service,
            to_node: str,
            namespace: str = None
    ):
        """Move a Pod from a node to another one
            we will create a new instance from a service with different name and remove previous one

        :param previousPod: V1Pod
            previous Pod

        :param previousService: V1Service
            previous Service

        :param to_node: str
            name of node which you want to start the pod in

        :param namespace: str
            namespace of Pod
        """
        # TODO: we should implement it
        #  get information of a Pod and change name that and create new one

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        try:
            previousPodName = get_pod_name(previousPod)
        except Exception as e:
            previousPodName = previousPod.metadata.name
            logger.error(e)

        if to_node == previousPod.spec.node_name:
            logger.info("[Migration] Pod '{}' exists in node '{}', so migration canceled.".format(
                previousPodName, previousPod.spec.node_name
            ))
            return previousPod, previousService

        logger.info("[Migration] Migrate Pod '{}' from Node '{}' to Node '{}' started ...".format(
            previousPodName, previousPod.spec.node_name, to_node
        ))

        # define new Name
        newName = generate_random_str()

        metadata: V1ObjectMeta = V1ObjectMeta(
            labels=previousPod.metadata.labels,
            name=newName
        )

        podSpec: V1PodSpec = previousPod.spec
        podSpec.hostname = previousPodName
        podSpec.node_name = to_node

        newPod = V1Pod(
            api_version=previousPod.api_version,
            metadata=metadata,
            spec=podSpec
        )

        logger.info("[Migration] Creating Pod '{}' in Node '{}'".format(
            previousPodName, newPod.spec.node_name
        ))
        createP = self.create_pod(newPod, namespace)
        if createP is None:
            logger.warn("[Migration] Creaing Pod faced an issue...")
            return None, previousService

        logger.info("Creating service '{}' ... ".format(newName))

        serviceSpec: V1ServiceSpec = previousService.spec
        serviceSpec.cluster_ip = None

        newService = V1Service(
            api_version=previousService.api_version,
            metadata=metadata,
            spec=previousService.spec
        )

        createS = self.create_service(newService)
        if createS is None:
            logger.error("can't create service '{}', so we will exit.. ".format(newName))
            return createP, None

        address = None
        for adr in self.node.status.addresses:
            if adr.type == 'ExternalIP':
                address = adr.address

        if address is None:
            logger.error('address of node "{}" does not exists.'.format(self.node))
            exit(-1)

        logger.info("Address of node is : '{}', so for connecting to utilization-server we will connect to it.".format(
            address
        ))

        request = requests.get('http://{}:{}/hostname/update/{}/{}/'.format(
            address, self.UTILIZATION_NODE_PORT, previousService.metadata.name, newName
        ))
        if request.status_code != 200:
            logger.error("response is: {}".format(request.content))
            exit(-1)

        logger.info("hostname information has been changed from '{}' to '{}'".format(
            previousPodName, newName
        ))

        logger.info("[Migartion] Deleting Previous Pod '{}' from Node '{}'".format(
            previousPodName, previousPod.spec.node_name
        ))
        self.delete_pod(previousPod.metadata.name, namespace)

        logger.info("[Migartion] Deleting Previous Service '{}'.".format(
            previousPodName
        ))
        self.delete_service(previousPod.metadata.name, namespace)

        logger.info("[Migration] Migration Done")
        return createP, createS

    def clean(self, namespace: str = None):
        """Clean all Pods of a namespace

        :param namespace: str
        """

        if namespace is None:
            # set default value for namespace
            namespace = self.namespace

        logger.info("Terminating Pods...")

        # delete all pods
        self._api.delete_collection_namespaced_pod(namespace)

        logger.info("Looking for namespace '{}'".format(
            namespace
        ))

        try:
            self._api.read_namespace(namespace)
        except ApiException as e:
            logger.warn("Namespace '{}' does not exist".format(
                namespace
            ))
            return True

        # remove namespace
        logger.info("Removing namespace '{}'".format(
            namespace
        ))
        self._api.delete_namespace(namespace)
        while True:
            time.sleep(1)
            try:
                self._api.read_namespace(namespace)
            except ApiException as e:
                logger.warn("namespace '{}' removed.".format(
                    namespace
                ))
                return True


class Cluster:
    """Kubernetes Cluster"""

    def __init__(
            self,
            config_file: str = None,
            namespace: str = None,
            workloads_path: str = None,
            utilization_server_image: str = None,
            cleaning_after_exiting: bool = False,
    ):
        """Kubnernetes Cluster Constructor

        :param config_file: str (default: ~/.kube/config)
            address of config file

        :param namespace: str (default: 'vpa')
            using namespace

        :param workloads_path: str (default: './data/workloads.pickle')
            path of workloads dataset

        :param utilization_server_image: str
            using this image to start utilization server (default: 'r0ot/utilization-server')

        :param cleaning_after_exiting: bool (default: False)
            clean the cluster after exiting
        """

        if config_file is None:
            # set default value for config_file
            config_file = '~/.kube/config'

        if namespace is None:
            # set default value for namespace
            namespace = 'vpa'

        if workloads_path is None:
            # set default value for workload_path
            workloads_path = './data/workloads.pickle'

        if utilization_server_image is None:
            # set default value for utilization server image
            utilization_server_image = 'r0ot/utilization-server'

        # define using namespace
        self.namespace = namespace

        # define config file
        self.config_file: str = config_file

        # define workloads path
        self.workloads_path: str = workloads_path

        # using utilization server image
        self.utilization_server_image: str = utilization_server_image

        # set config file for client
        config.load_kube_config(self.config_file)

        # define client interface (general api)
        self._api = CoreV1Api()

        # define object interface (using for metrics)
        self._object_api = CustomObjectsApi()

        # define monitoring interface
        self.monitor = Monitor(
            self._api,
            self._object_api,
            self.namespace,
        )

        # determine handling signals
        self.cleaning_after_exiting = cleaning_after_exiting

        # Choose  Node
        nodes = self.monitor.get_nodes()

        # define action interface
        self.action = Action(
            self._api,
            self._object_api,
            self.namespace,
            self.workloads_path,
            self.utilization_server_image,
            nodes[0],
            self.cleaning_after_exiting,
        )
