import setuptools

setuptools.setup(
    name="envoy-logger",
    version="1.1.0",
    packages=setuptools.find_packages(exclude=["test"]),
    include_package_data=True,
    python_requires='>=3.6',
    install_requires=[
        "requests",
        "appdirs",
        "influxdb-client",
        "PyYAML",
    ],
)
