"""
Main module, it must be executed as a script with python3 in order to run the program.

This script runs the function run_main from the Starling framework.

For more information about the required and available options, run

```bash
python3 main.py -h
```
"""

from starling_sim.model_simulator import run_main


if __name__ == "__main__":

    # run the function from model_simulator which will parse the provided arguments
    run_main()
