import os
import sys
import click
import json
import pickle
import numpy as np

import gym

import smart_vpa # noqa
from smart_vpa.recommender import (
    Threshold,
    Random,
    Builtin,
    RL,
    LSTM
)
from smart_vpa.util import (
    logger)

# get an absolute path to the directory that contains parent files
project_dir = os.path.dirname(os.path.join(os.getcwd(), __file__))
sys.path.append(os.path.normpath(os.path.join(project_dir, '..', '..')))

from experiments.utils.constants import ( # noqa
    CONFIGS_PATH
)
from experiments.utils import build_config


def check_env(env, recommender):
    done = False
    _ = env.reset()
    _ = recommender.reset()
    while not done:
        timestamp = env.wall_time
        observation = env.observation
        recommender.update(observation=observation, timestamp=timestamp)
        action = recommender.recommender()
        observation, reward, done, info = env.step(action)
        log_action = {
            "memory": action[[0, 2, 4]].tolist(), # Y
            "cpu": action[[1, 3, 5]].tolist()
        }
        logger.info(log_action)
        env.render()


@click.command()
@click.option('--type-env', required=True,
              type=click.Choice(['sim', 'kube']),
              default='sim')
@click.option('--type-recommender', required=True,
              type=click.Choice(['builtin', 'random', 'threshold',
                                 'lstm', 'rl']),
              default='builtin')
@click.option('--workload-id', required=True, type=int, default=1)
@click.option('--round-robin', required=True, type=bool, default=True)
@click.option('--seed', required=True, type=int, default=100)
def main(
    type_env: str,
    type_recommender: str,
    workload_id: int,
    round_robin: bool,
    seed: int
        ):
    """
    """
    # -------------- load container config and workload --------------
    config = build_config(
        workload_id=workload_id,
        seed=seed,
        round_robin=round_robin)

    # picking the right environment
    type_env = {
        'sim': 'SimEnv-v0',
        'kube': 'KubeEnv-v0'
    }[type_env]
    env = gym.make(type_env, config=config)

    # -------------- make the recommender --------------
    # load recommender config
    container_file_path = os.path.join(
        CONFIGS_PATH, 'recommender', f"{type_recommender}.json")
    try:
        with open(container_file_path) as cf:
            config = json.loads(cf.read())
    except FileNotFoundError:
        print(f"recommender {type_recommender} does not exist")

    # add the action space of the environment to the config
    config.update({'action_space': env.action_space})

    # passing the approperiate recommender
    recommender = {
        'threshold': Threshold,
        'random': Random,
        'builtin': Builtin,
        'rl': RL,
        'lstm': LSTM
        }[type_recommender](config=config)

    # if it's an ML method then load the saved model
    base_class = repr(recommender.__class__.__bases__)
    if 'MLInterface' in base_class:
        # TODO load a saved model
        # TODO recommender.load(model=model)
        pass

    # -------------- run the environment --------------
    check_env(
        env=env,
        recommender=recommender)


if __name__ == "__main__":
    main()
