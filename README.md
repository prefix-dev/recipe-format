# New `recipe.yaml` format schema

This repository contains the [JSON Schema](./schema.json) for the new `recipe.yaml` format proposed in the following conda CEPs:

- https://github.com/conda-incubator/ceps/pull/54
- https://github.com/conda-incubator/ceps/pull/56
- https://github.com/conda-incubator/ceps/pull/57 (not yet implemented)

And [Variant Schema](./variant_schema.json) for the `variant_config.yaml` files.

## How to use 

There is a fully JSON Schema 1.0 compliant [schema.json](./schema.json) at the root of this repository. 
This file is generated from the `model.py` using `pydantic`.

You can use the schema in any editor that supports JSON Schema for yaml. 
Using the YAML extension for VSCode all you need to do is add: 

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/prefix-dev/recipe-format/main/schema.json
```

to the top of your recipe file and you should have autocompletion and validation!

Similarly for that `variant_schema.json` add,

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/prefix-dev/recipe-format/main/variant_schema.json
```

## Contributing

The project is using [`pixi`](https://github.com/prefix-dev/pixi) to be able to quickly format, validate and generate the schema.

Note: When submitting changes to `model.py` make sure to run following commands locally first.(inorder)

```sh
pixi run fmt
pixi run lint
pixi run generate > schema.json
pixi run genvariant > variant_schema.json
pixi run test 
```




