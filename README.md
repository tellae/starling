# Starling

**Starling** is an agent-based simulation framework for urban mobility.

It provides generic classes to build transport models such as station-based sharing system,
public transport or shared taxis.

**Citation info**: Leblond, V, Desbureaux, L, Bielecki, V., 2020. "[A new agent-based software for designing and optimizing emerging mobility services : application to city of Rennes](https://aetransport.org/past-etc-papers/conference-papers-2020?abstractId=6706&state=b)." *Proceedings of the European Transport Conference*, 11 September 2020, Milan

![](./docs/images/starling-viz.gif)

## License

[CeCILL-B](LICENSE.txt)

Feel free to use and contribute to **Starling** project as long as you comply with the licence terms.

## Quickstart

This section will show you how to run the example simulation scenarios.

For a more detailed setup guide, see the section
[Running simulations](https://starling.readthedocs.io/en/latest/run/running_simulations.html)
of the documentation.

### Installation

The *starling-sim* package is available on PiPy and can be installed using pip:

```bash
pip install starling-sim
```

You can check that the package was correctly installed by running the `starling-sim` command:

```bash
starling-sim --version
```

### Examples

If you need example scenarios, you can download the test scenarios from the repository.

If you cloned the Starling repository, you can also run the following command:

```bash
starling-sim data --examples
```

### Usage

Once the data is prepared, a scenario can be run from the project
root by running the `starling-sim` command with the path to the scenario folder. 
For instance:

```bash
starling-sim run data/models/SB_VS/example_nantes/
```

You will see the progression of the simulation with the logs that
appear in the console.

### Outputs

You can find the outputs of the scenario in the output folder.
In this case, its data/models/SB_VS/example_nantes/outputs/.

KPI files (.csv.gz) can be visualised with any spreadsheet software.

The visualisation file (.geojson) can be uploaded to the web application
[Kite](https://kite.tellae.fr/) to visualise the simulation run.

## Documentation

The project documentation is generated using Sphinx and hosted by *Read the Docs* here:

<https://starling.readthedocs.io/en/latest/>

The documentation is still incomplete, but contributions and suggestions are very welcome.

## Contributing

Feedback and contributions on Starling, the code, the documentation or
even the github management are very welcome.

We haven't established a contributing procedure yet, but we will do our
best to guide you if you want to contribute to this project.

## Support

You can email us at starling@tellae.fr for any support demand.

## Project status

[*Tellae*](https://tellae.fr/) is actively contributing to Starling as part of its research and development activities.

Tellae uses Starling in commercial contracts to study mobility projects. This is why
some of the models and algorithms developed around Starling are not shared in this repository.
