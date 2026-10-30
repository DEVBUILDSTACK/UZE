"""Shared base for GENERATED Pydantic models.

datamodel-code-generator is invoked with --base-class base.FrozenModel, so
every generated model (including nested ones like Price) inherits this
frozen config. The frozen config therefore survives regeneration: it is a
generation input, not an edit to a generated file.
"""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    # frozen: snapshots are immutable once quoted.
    # extra="forbid": the contract is closed — an unexpected field is an
    # error, not something to silently carry. This also makes the exported
    # JSON Schema carry additionalProperties: false, so the generated
    # TypeScript is strict (no index-signature loosening).
    model_config = ConfigDict(frozen=True, extra="forbid")
