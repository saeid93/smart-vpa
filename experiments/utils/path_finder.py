"""
change the ids to full paths
"""
import json
import os
import pickle
import sys
import numpy as np
from typing import Union, Any, Dict

# get an absolute path to the directory that contains parent files
project_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
sys.path.append(os.path.normpath(os.path.join(project_dir, '..', '..')))

from experiments.utils.constants import (
    DATASETS_PATH,
    WORKLOADS_PATH,
    CONFIGS_PATH
    )


def build_config(
    workload_id: int,
    seed: int,
    round_robin: bool) -> Dict[str, Any]:


    config: dict = {}
    workload: np.array = np.array([])
    time: np.array = np.array([])
    workload_path = os.path.join(
        WORKLOADS_PATH, 'synthetic', str(workload_id))

    # load container config
    # container initial requests and limits
    container_file_path = os.path.join(workload_path, "container.json")
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

    # -------------- make the environment --------------
    # update the passed config to the environment
    config.update({
        'workload': workload,
        'seed': seed,
        'round-robin': round_robin,
        'time': time})
    return config
