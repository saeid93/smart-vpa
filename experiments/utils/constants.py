import os
from mobile_kube.envs import (
    SimEdgeEnv,
    SimBinpackingEnv,
    SimGreedyEnv,
    KubeEdgeEnv,
    KubeBinpackingEnv,
    KubeGreedyEnv
)

# dfined by the user
DATA_PATH = "/Users/saeid/Codes/smart-vpa/smart-vpa/data"
# generated baesd on the users' path
DATASETS_PATH = os.path.join("/Users/saeid/Codes/mobile-kube/data", "datasets")
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

ENVS = {
    'sim-edge': SimEdgeEnv,
    'sim-binpacking': SimBinpackingEnv,
    'sim-greedy': SimGreedyEnv,
    'kube-edge': KubeEdgeEnv,
    'kube-binpacking': KubeBinpackingEnv,
    'kube-greedy': KubeGreedyEnv
}

ENVSMAP = {
    'sim-edge': 'SimEdgeEnv-v0',
    'sim-binpacking': 'SimBinpackingEnv-v0',
    'sim-greedy': 'SimGreedyEnv-v0',
    'kube-edge': 'KubeEdgeEnv-v0',
    'kube-binpacking': 'KubeBinpackingEnv-v0',
    'kube-greedy': 'KubeGreedyEnv-v0',
}
