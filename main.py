from tiozin.assembly.plugin_factory import plugin_factory
from tiozin.family.tio_kernel.inputs.noop_input import NoOpInput

NoOpInput()

plugin_factory.setup()
# for i in plugin_factory._plugins:
#     print(i)

# result = helpers.scan_classes(
#     root=tio_kernel,
#     predicate=helpers.is_plugin,
# )

# for i in result:
#     print(i)


# plugin = registry.get("FileJobRegistry")
# print(plugin)

# from tiozin.family.tio_kernel.inputs.noop_input import NoOpInput
# from tiozin.family.tio_kernel.registries import PluginFactory

# register = PluginFactory()
# register.register(NoOpInput)

plugin_manifest = {
    "org": "test",
    "region": "test",
    "domain": "test",
    "product": "test",
    "model": "test",
    "layer": "test",
    "kind": "NoOpInput",
    "name": "ReadNothing",
    "description": "just a test",
}

input = plugin_factory.get_input(**plugin_manifest)

# print(input)
# print(input.id)
# print(input.kind)
# print(input.name)
# print(input.description)
# input.read(None)
