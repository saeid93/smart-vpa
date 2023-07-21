from entities.cluster import Cluster
from utils import construct_pod, construct_svc

# Cluster Configurations
CONFIG_FILE = './kube.conf'
NAMESPACE = 'vpa'
WORKLPAD_PATH = './data/workload.pickle'
UTILIZATION_IMAGE = 'r0ot/utilization-server'


# Pod Configurations
POD_SVC_NAME = 'sample-vpa'
POD_IMAGE = 'r0ot/stress'


# create Cluster and create utilization-server
cluster = Cluster(
    config_file=CONFIG_FILE,
    namespace=NAMESPACE,
    workloads_path=WORKLPAD_PATH,
    utilization_server_image=UTILIZATION_IMAGE,
)

# construct a pod
pod = construct_pod(
    name=POD_NAME,
    image=POD_IMAGE,
    namespace=NAMESPACE,
)

# construct a service
svc = construct_svc(
    name=POD_SVC_NAME,
    namespace=NAMESPACE,
)

"""apply pod and service of application onto the cluster"""

# apply pod
cluster.action.create_pod(pod)

# apply svc
cluster.action.create_service(svc)

