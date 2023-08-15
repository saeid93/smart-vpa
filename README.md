## Prerequisite
1. Install vertical pod autoscaler with on of the following methods
   1. [Kubernetes open source autoscaler installation](https://cloud.google.com/kubernetes-engine/docs/how-to/vertical-pod-autoscaling)
   2. [Google cloud installation](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)

2. Go to the [/smart_vpa](./smart_vpa) and install the framework in editable mode
   ```bash
   pip install -e .
   ```
3. Go to [/experiments/utils/constants.py](/experiments/utils/constants.py) and set the path to your data and project folders in the file. For example:
   ```bash
   DATA_PATH = "/Users/saeid/Codes/arabesque/smart-vpa/data"
   ```

## [Generating the Workloads](experiments/workload/generate_workload.py)

1. Go to the your dataset generation config [data/configs/workloads](data/configs/workloads) and choose the apporoperiate config e.g. for step workloads you can change the variables in [data/configs/workloads/step.json](data/configs/workloads/step.json)
```bash
python generate_workload.py --help
Usage: generate_workload.py [OPTIONS]

Options:
  --workload-type TEXT
  --help                Show this message and exit.
```

