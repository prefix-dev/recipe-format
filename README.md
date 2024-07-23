# New `recipe.yaml` format schema

This repository contains the [JSON Schema](https://github.com/prefix-dev/recipe-format/blob/main/schema.json) for the new `recipe.yaml` format as described in the following conda CEPs:

- [CEP 13 - A new Recipe format (Part 1)](https://github.com/conda/ceps/blob/main/cep-13.md)
- [CEP 14 - A new Recipe format (Part 2) - the allowed keys & values](https://github.com/conda/ceps/blob/main/cep-14.md)

## How to use 

There is a fully JSON Schema 1.0 compliant [schema.json](./schema.json) at the root of this repository. 
This file is generated from the `model.py` using `pydantic`.

You can use the schema in any editor that supports JSON Schema for yaml. 
Using the YAML extension for VSCode all you need to do is add: 

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/prefix-dev/recipe-format/main/schema.json
```

to the top of your recipe file and you should have autocompletion and validation!

## Contributing

The project is using [`pixi`](https://github.com/prefix-dev/pixi) to be able to quickly format, validate and generate the schema.

Note: When submitting changes to `model.py` make sure to run following commands locally first.(inorder)

```sh
pixi run fmt
pixi run lint
pixi run generate
pixi run test 
```




