import datetime as dt
import json
import time

import tqdm
from quick_one_liner_lookup import prompter
from quick_one_liner_lookup.custom_types import Dataset
from quick_one_liner_lookup.utils import get_current_model, get_dataset_location


def load_dataset() -> Dataset:
    with open(get_dataset_location(), "r") as f:
        return json.load(f)


def sample_dataset(dataset: Dataset, every_nth: int = 100):
    return dataset[::every_nth]


def benchmark(benchmark_dataset: Dataset) -> None:
    # Prompt to get results
    inputs = []
    results = []
    expected_results = []
    times = []

    for dataset_entry in tqdm.tqdm(benchmark_dataset):
        dataset_input = dataset_entry["input"]
        inputs.append(dataset_input)
        dataset_output = dataset_entry["output"]
        start_time = time.time()
        result = prompter.prompt(dataset_input)
        times.append(time.time() - start_time)
        results.append(result)
        expected_results.append(dataset_output)

    with open(f"results_{int(dt.datetime.now().timestamp()*1e6)}_{get_current_model()}.csv", "w") as f:
        for current_input, current_result, expected_result, execution_time in zip(inputs, results, expected_results, times):
            f.write(f'"{current_input}"\t{current_result}\t{expected_result}\t{execution_time:.3f}\n')


if __name__ == "__main__":
    benchmark_dataset = sample_dataset(dataset=load_dataset(), every_nth=500)
    benchmark(benchmark_dataset=benchmark_dataset)
