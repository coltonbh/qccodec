# qccodec

A library for parsing Quantum Chemistry output files into structured data objects and converting structured input objects into program-native input files. Uses data structures from [qcio](https://github.com/coltonbh/qcio).

[![image](https://img.shields.io/pypi/v/qccodec.svg)](https://pypi.python.org/pypi/qccodec)
[![image](https://img.shields.io/pypi/l/qccodec.svg)](https://pypi.python.org/pypi/qccodec)
[![image](https://img.shields.io/pypi/pyversions/qccodec.svg)](https://pypi.python.org/pypi/qccodec)
[![Actions status](https://github.com/coltonbh/qccodec/workflows/Tests/badge.svg)](https://github.com/coltonbh/qccodec/actions)
[![Actions status](https://github.com/coltonbh/qccodec/workflows/Basic%20Code%20Quality/badge.svg)](https://github.com/coltonbh/qccodec/actions)

`qccodec` works in harmony with a suite of other quantum chemistry tools for fast, structured, and interoperable quantum chemistry.

## The QC Suite of Programs

- [qcconst](https://github.com/coltonbh/qcconst) - Physical constants, conversion factors, and a periodic table with clear source information for every value.
- [qcio](https://github.com/coltonbh/qcio) - Beautiful and user friendly data structures for quantum chemistry.
- [qccodec](https://github.com/coltonbh/qccodec) - A library for efficient parsing of quantum chemistry data into structured `qcio` objects and conversion of `qcio` input objects to program-native input files.
- [qcop](https://github.com/coltonbh/qcop) - A package for operating quantum chemistry programs using `qcio` standardized data structures. Compatible with `TeraChem`, `psi4`, `QChem`, `NWChem`, `ORCA`, `Molpro`, `geomeTRIC` and many more.
- [BigChem](https://github.com/mtzgroup/bigchem) - A distributed application for running quantum chemistry calculations at scale across clusters of computers or the cloud. Bring multi-node scaling to your favorite quantum chemistry program.
- `ChemCloud` - A [web application](https://github.com/mtzgroup/chemcloud-server) and associated [Python client](https://github.com/mtzgroup/chemcloud-client) for exposing a BigChem cluster securely over the internet.

## ✨ Basic Usage

- Installation:

  ```sh
  python -m pip install qccodec
  ```

- Parse QC program outputs into structured data files with a single line of code.

  ```python
  from pathlib import Path
  from qcio import CalcType
  from qccodec import decode

  stdout = Path("tc.out").read_text()
  data = decode("terachem", CalcType.gradient, stdout=stdout)
  ```

- The `data` object will be a `qcio` object, either `SinglePointData`, `OptimizationData`, `ConformerSearchData` or other `*Data` structure depending on the `calctype`. Run `dir(data)` inside a Python interpreter to see the various values you can access. A few prominent values are shown here as an example:

  ```python
  from pathlib import Path
  from qcio import CalcType
  from qccodec import decode

  stdout = Path("tc.out").read_text()
  data = decode("terachem", CalcType.hessian, stdout=stdout)

  data.energy
  data.gradient # If a gradient calc
  data.hessian # If a hessian calc
  data.calcinfo_nmo # Number of molecular orbitals
  ```

- Parsed values can be written to disk like this:

  ```py
  with open("data.json", "w") as f:
      f.write(data.model_dumps_json())
  ```

- And read from disk like this:

  ```py
  from qcio import SinglePointData

  data = SinglePointData.open("data.json")
  ```

- You can also run `qccodec` from the command line like this:

  ```sh
  qccodec -h # Get help message for cli

  qccodec terachem hessian tests/data/terachem/water.frequencies.out > data.json # Parse TeraChem stdout to json
  ```

- More complex parsing can be accomplished by passing the directory containing the scratch files to `decode` and optionally the input data used to generate the calculation (usually done from `qcop` which uses structure data):

  ```python
  from pathlib import Path
  from qcio import CalcType, ProgramInput
  from qccodec import decode

  stdout = Path("tc.out").read_text()
  directory = Path(".") / "scr.geom"
  input_data = ProgramInput.open("prog_inp.json")

  data = decode("terachem", CalcType.hessian, stdout=stdout, directory=directory, input_data=input_data)
  ```

## 💻 Contributing

Please see the [contributing guide](./CONTRIBUTING.md) for details on how to contribute new parsers to this project :)

If there's data you'd like parsed from output files or want to support input files for a new program, please open an issue in this repo explaining the data items you'd like parsed and include an example output file containing the data, like [this](https://github.com/coltonbh/qccodec/issues/2).
