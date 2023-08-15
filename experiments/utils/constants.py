import os
from smart_vpa.envs import (
    SimEnv,
    KubeEnv
)

# dfined by the user
DATA_PATH = "/home/cc/smart-vpa/data"

# generated baesd on the users' path
TRAIN_RESULTS_PATH = os.path.join(DATA_PATH, "train-results")
TESTS_RESULTS_PATH = os.path.join(DATA_PATH, "test-results")
CONFIGS_PATH = os.path.join(DATA_PATH, "configs")

# generated baesd on the users' path
WORKLOADS_PATH = os.path.join(DATA_PATH, "workloads")
RESULTS_PATH = os.path.join(DATA_PATH, "results")
ARABESQUE_PATH = os.path.join(DATA_PATH, "arabesque-raw")
ALIBABA_PATH = os.path.join(DATA_PATH, "alibaba-raw")
ANALYSIS_CONTAINERS_PATH = os.path.join(
    DATA_PATH, "analysis", "containers")
ANALYSIS_CLUSTERS_PATH = os.path.join(
    DATA_PATH, "analysis", "clusters")
FINAL_STATS_PATH = os.path.join(
    DATA_PATH, "final_stats"
)
FIGURES_PATH = os.path.join(
    DATA_PATH, "figures"
)

ENVS = {
    'sim': SimEnv,
    'kube': KubeEnv
}
