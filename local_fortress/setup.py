from setuptools import setup, find_packages

setup(
    name="qorelogic-gatekeeper",
    version="2.1.0",
    description="QoreLogic Sovereign Gatekeeper - MCP Server & Active Governance Hook",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.0.0",
        "cryptography>=41.0.0",
        "pydantic>=2.0.0",
        "requests",
        "typing_extensions"
    ],
    entry_points={
        'console_scripts': [
            'qorelogic-server=mcp_server.server:main', # Assuming we invoke mcp.run() manually or fastmcp has a runner
            'qorelogic-check=qorelogic_gatekeeper.cli:main',
        ],
    },
    python_requires='>=3.10',
)
