# connector-runtime Specification

## Purpose
Defines the MCP connector runtime: an MCP server built on the official Python SDK (FastMCP) via a stateless factory, a trivial `ping` health tool proving the request path, environment-driven immutable configuration with validation, and a single runnable entry point.

## Requirements

### Requirement: Connector is an MCP server built on the official SDK
The connector SHALL be implemented as a Model Context Protocol (MCP) server using the official MCP Python SDK (FastMCP). A factory function SHALL build and return a configured server instance with its tools registered, holding no shared mutable module state.

#### Scenario: Building a server registers its tools
- **WHEN** the server factory is called with a valid configuration
- **THEN** it returns an MCP server instance whose registered tools include the `ping` tool

#### Scenario: Each build is independent
- **WHEN** the server factory is called twice
- **THEN** it returns two independent server instances (building one does not mutate global state shared with the other)

#### Scenario: Edge case — tool input schema is derived from type hints
- **WHEN** the server lists its tools
- **THEN** each tool exposes a name and an input schema derived from its type-hinted signature, with no untyped parameters

### Requirement: A trivial health tool proves the request path
The connector SHALL expose one trivial, pure tool named `ping` that takes no arguments and returns a constant string, demonstrating the end-to-end tool request/response path with no external dependencies.

#### Scenario: Ping returns a constant response
- **WHEN** the `ping` tool is invoked
- **THEN** it returns the string `"pong"`

#### Scenario: Ping is pure
- **WHEN** the `ping` tool is invoked multiple times
- **THEN** it returns the same value every time and performs no side effects or network calls

### Requirement: Configuration is loaded and validated from the environment
The connector SHALL build its configuration from environment variables into an immutable configuration value, applying defaults for unset variables and rejecting invalid values with a clear error. The configuration SHALL include the transport, host, port, and log level.

#### Scenario: Defaults apply when variables are unset
- **WHEN** configuration is built from an empty environment
- **THEN** it yields the documented defaults (transport `stdio`, host `127.0.0.1`, port `8000`, log level `INFO`)

#### Scenario: Environment overrides are applied
- **WHEN** the transport, host, port, and log level variables are set to valid values
- **THEN** the resulting configuration reflects those values with the correct types (e.g. port as an integer)

#### Scenario: Edge case — invalid transport is rejected
- **WHEN** the transport variable is set to an unsupported value (e.g. `carrier-pigeon`)
- **THEN** building the configuration raises a configuration error identifying the invalid transport, rather than returning a server that fails later

#### Scenario: Edge case — non-integer port is rejected
- **WHEN** the port variable is set to a non-integer value (e.g. `abc`)
- **THEN** building the configuration raises a configuration error identifying the invalid port

### Requirement: The connector is runnable via a single entry point
The package SHALL provide a runnable entry point (`python -m ynab_claude_connector`, and an equivalent console script) that loads configuration from the environment, configures logging, builds the server, and starts it using the configured transport.

#### Scenario: Module entry point starts the configured server
- **WHEN** the package is executed as a module with a valid environment
- **THEN** it builds the server from environment configuration and starts it on the configured transport (defaulting to `stdio`)

#### Scenario: Edge case — invalid configuration fails fast at startup
- **WHEN** the package is executed with an invalid configuration value in the environment
- **THEN** startup raises the configuration error before the server begins serving, surfacing the misconfiguration immediately
