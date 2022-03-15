"""
change the ids to full paths
"""
import json
from ntpath import join
import os
import pickle
import sys
import numpy as np
from typing import List, Union, Any, Dict

# get an absolute path to the directory that contains parent files
project_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
sys.path.append(os.path.normpath(os.path.join(project_dir, '..', '..')))

from experiments.utils.constants import (
    DATASETS_PATH,
    WORKLOADS_PATH,
    CONFIGS_PATH
    )


def transform(
    configs: List[
        Dict[str, Any]]) -> Dict[str, List]:
    trans_config = {}
    keys = configs[0].keys()
    trans_config = dict(zip(keys, [[] for i in range(len(keys))]))
    for config in configs:
        for key in keys:
            trans_config[key].append(config[key])
    return trans_config



def build_config(
    workload_id: int,
    seed: int,
    round_robin: bool,
    workload_bunch: int,
    workload_type: str,
    workload_full_path=""
    ) -> List[Dict[str, Any]]:

    if workload_type=='synthetic':
        workload_path = os.path.join(
            WORKLOADS_PATH, workload_type, str(workload_id))
    elif workload_type=='arabesque':
        workload_path = os.path.join(
            WORKLOADS_PATH, workload_type, workload_full_path)

    workloads_path = sorted(os.listdir(workload_path))
    workloads_path.remove('.DS_Store')
    workloads_path_selected = workloads_path[0:workload_bunch]
    workloads_path_selected = list(
        map(
            lambda a: os.path.join(workload_path, a), workloads_path))

    # workloads = []
    # times = []
    configs = []
    for workload_path in workloads_path_selected:
        config: dict = {}
        workload: np.array = np.array([])
        time: np.array = np.array([])
        # load container config
        # container initial requests and limits
        container_file_path = os.path.join(
            workload_path, "container.json")
        try:
            with open(container_file_path) as cf:
                config = json.loads(cf.read())
        except FileNotFoundError:
            print(f"workload {workload_id} does not have a container")

        # load the workoad
        workload_file_path = os.path.join(workload_path, 'workload.pickle')
        try:
            with open(workload_file_path, 'rb') as in_pickle:
                workload = pickle.load(in_pickle)
        except FileNotFoundError:
            raise Exception(f"workload {workload_id} does not exists")

        # load the time array of the workload
        time_file_path = os.path.join(workload_path, 'time.pickle')
        try:
            with open(time_file_path, 'rb') as in_pickle:
                time = pickle.load(in_pickle)
        except FileNotFoundError:
            raise Exception(f"workload {workload_id} does not have time array")

        # workloads.append(workload)
        # times.append(time)
        config.update({
            'workload': workload,
            'seed': seed,
            'round-robin': round_robin,
            'time': time})
        configs.append(config)
    
    trans_config = transform(configs)

    return trans_config
