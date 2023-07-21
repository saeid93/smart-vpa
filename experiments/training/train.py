import os
import sys
import shutil
import click
from typing import Dict, Any
import json

import ray
from ray import tune
from ray.rllib.utils.framework import try_import_torch
import pprint

# get an absolute path to the directory that contains parent files
project_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
sys.path.append(os.path.normpath(os.path.join(project_dir, '..', '..')))

from experiments.utils.constants import (
    TRAIN_RESULTS_PATH,
    CONFIGS_PATH,
)
from experiments.utils import (
    build_config,
    make_env_class,
    CloudCallback
)

torch, nn = try_import_torch()


def learner(*, config_file_path: str, config: Dict[str, Any],
            series: int, type_env: str,
            workload_id: int,
            workload_type: str,
            workload_full_path: str,
            workload_bunch: int,
            use_callback: bool,
            round_robin:bool,
            checkpoint_freq: int,
            local_mode: bool,
            seed: int):
    """
    input_config: {"env_config_base": ...,
                    "run_or_experiment": ...,
                    "learn_config": ...,
                    "stop": ...}
    - is used to build:
    ray_config: {...
                learning paramters
                ...,
                env: <environment class>,
                env_config: <environment config read before>
                }

    - the results are saved into the concatenation of the following paths:
        - results path:
          data/results/
        - environment info:
          env/<env_id>/datasets/<dataset_id>/workloads/<workload_id>
          /experiments/<experiment_id>
        - rllib:
          <name_of_algorithm>/<trial>
    """
    # extract differnt parts of the input_config
    stop = config['stop']
    learn_config = config['learn_config']
    run_or_experiment = config["run_or_experiment"]

    # add the additional nencessary arguments to the edge config
    env_config = build_config(
        workload_id=workload_id,
        workload_type=workload_type,
        workload_full_path=workload_full_path,
        workload_bunch=workload_bunch,
        seed=seed,
        round_robin=round_robin,
        )

    # generate the ray_config
    # make the learning config based on the type of the environment
    if type_env not in ['CartPole-v0', 'Pendulum-v0']:
        ray_config = {"env": make_env_class(type_env),
                    "env_config": env_config}
    else:
        ray_config = {"env": type_env}

    # generate the path
    # folder formats: <environmet>/datasets/<dataset>/workloads/<workload>
    # example:        env1/dataset/1/workloads/3
    experiments_folder = os.path.join(TRAIN_RESULTS_PATH,
                                      "series",     str(series),
                                      "envs",       str(type_env),
                                      "workloads",  str(workload_id),
                                      "experiments")
    # make the base path if it does not exists
    if not os.path.isdir(experiments_folder):
        os.makedirs(experiments_folder)
    # generate new experiment folder
    content = os.listdir(experiments_folder)
    new_experiment = len(content)
    this_experiment_folder = os.path.join(experiments_folder,
                                          str(new_experiment))
    # make the new experiment folder
    os.mkdir(this_experiment_folder)

    # copy our input json to the path a change
    # the name to a unified name
    shutil.copy(config_file_path, this_experiment_folder)
    source_file = os.path.join(this_experiment_folder,
                               os.path.split(config_file_path)[-1])
    dest_file = os.path.join(this_experiment_folder, 'experiment_config.json')
    os.rename(source_file, dest_file)

    # update the ray_config with learn_config
    ray_config.update(learn_config)

    # if callback is specified add it here
    if use_callback and\
        type_env not in ['CartPole-v0', 'Pendulum-v0']:
        ray_config.update({'callbacks': CloudCallback})

    ray.init(local_mode=local_mode)
    # run the ML after fixing the folders structres
    _ = tune.run(local_dir=this_experiment_folder,
                 run_or_experiment=run_or_experiment,
                 config=ray_config,
                 stop=stop,
                 checkpoint_freq=checkpoint_freq,
                 checkpoint_at_end=True)

    # delete the unnecessary big json file
    # TODO maybe of use in the analysis
    this_experiment_trials_folder = os.path.join(
        this_experiment_folder, run_or_experiment)
    this_experiment_trials_folder_contents = os.listdir(
        this_experiment_trials_folder)
    for item in this_experiment_trials_folder_contents:
        if 'json' in item:
            json_file_name = item
            break
    json_file_path = os.path.join(
        this_experiment_trials_folder,
        json_file_name)
    os.remove(json_file_path)


@click.command()
@click.option('--local-mode', type=bool, default=True)
@click.option('--config-file', type=str, default='A2C')
@click.option('--series', required=True, type=int, default=71)
@click.option('--type-env', required=True,
              type=click.Choice(['sim', 'kube']),
              default='sim')
@click.option('--workload-id', required=True, type=int, default=1)
@click.option('--workload-type', required=True,
              type=click.Choice(['alibaba', 'synthetic', 'arabesque']),
              default='arabesque')
@click.option('--workload-full-path', required=True, type=str,
              default='engine-top-ten/engine')
@click.option('--workload-bunch', required=True, type=int,
              default=10)
@click.option('--round-robin', required=True, type=bool, default=True)
@click.option('--use-callback', required=True, type=bool, default=False)
@click.option('--checkpoint-freq', required=False, type=int, default=1000)
@click.option('--seed', required=False, type=int, default=1000)
def main(local_mode: bool, config_file: str, series: int,
         type_env: str, workload_id: int, workload_type: str,
         workload_full_path: str, workload_bunch: int,
         round_robin: bool, use_callback: bool, checkpoint_freq: int,
         seed: int):
    """[summary]

    Args:
        local_mode (bool): run in local mode for having the 
        config_file (str): name of the config folder (only used in real mode)
        use_callback (bool): whether to use callbacks or storing and visualising
        checkpoint_freq (int): checkpoint the ml model at each (n-th) step
        series (int): to gather a series of datasets in a folder
        type_env (str): the type of the used environment
        dataset_id (int): used cluster dataset
        workload_id (int): the workload used in that dataset
        workload_type (str): the type of the workload
        workload_full_path (str): full workload foldering paths
        workload_bunch (int)L: number of workloads given as a bunch
    """
    config_file_path = os.path.join(
        CONFIGS_PATH, 'train', f"{config_file}.json")
    with open(config_file_path) as cf:
        config = json.loads(cf.read())

    pp = pprint.PrettyPrinter(indent=4)
    print('start experiments with the following config:\n')
    pp.pprint(config)

    learner(config_file_path=config_file_path,
            config=config, series=series,
            type_env=type_env,
            workload_id=workload_id,
            workload_type=workload_type,
            workload_full_path=workload_full_path,
            workload_bunch=workload_bunch,
            round_robin=round_robin, use_callback=use_callback,
            checkpoint_freq=checkpoint_freq, local_mode=local_mode,
            seed=seed)


if __name__ == "__main__":
    main()
