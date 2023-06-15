# New `recipe.yaml` format schema

This repository contains the [JSON Schema](./schema.json) for the new `recipe.yaml` format proposed in the following conda CEPs:

- https://github.com/conda-incubator/ceps/pull/54
- https://github.com/conda-incubator/ceps/pull/56
- https://github.com/conda-incubator/ceps/pull/57 (not yet implemented)

## How to use 

There is a fully JSON Schema 1.0 compliant [schema.json](./schema.json) at the root of this repository. 
This file is generated from the `model.py` using `pydantic`.

You can use the schema in any editor that supports JSON Schema for yaml. 
Using the YAML extension for VSCode all you need to do is add: 




## Contributing

The project is using [`pixi`](https://github.com/prefix.dev/pixi) to be able to quickly format, validate and generate the schema.



