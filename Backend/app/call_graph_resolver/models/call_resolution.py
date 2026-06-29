
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CallKind(str,
Enum):
    """The three mutually exclusive call categories."""
    INTERNAL   = "internal"    # callee lives in the same file
    CROSS_FILE = "cross_file"  # callee lives in a different file in the repo
    EXTERNAL   = "external"    # callee comes from a third-party / stdlib import


class ResolutionStatus(str,
Enum):
    RESOLVED   = "resolved"    # callee id / library confirmed
    AMBIGUOUS  = "ambiguous"   # multiple candidates match
    UNRESOLVED = "unresolved"  # no candidate found


@dataclass(frozen=True)
class ResolvedCall:
    """
    The canonical output of any resolver.

    Fields
    ------
    caller_id       UUID of the calling FunctionInfo chunk.
    callee_id       UUID of the called FunctionInfo chunk (None for external calls).
    call_kind       INTERNAL | CROSS_FILE | EXTERNAL
    function_name   Raw call expression as extracted by the chunker (e.g. "obj.method").
    call_line       Source line of the call site.
    status          Whether resolution succeeded,
    was ambiguous,
    or failed.
    library         Import path for external calls (e.g. "os.path",
    "requests").
    resolved_path   File path of the callee's file for cross-file calls.
    candidates      All matching chunk ids when status is AMBIGUOUS.
    note            Human-readable explanation attached when status != RESOLVED.
    """
    caller_id:     str
    function_name: str
    call_kind:     CallKind
    status:        ResolutionStatus

    callee_id:     Optional[str]       = None
    call_line:     Optional[int]       = None
    library:       Optional[str]       = None
    resolved_path: Optional[str]       = None
    candidates:    tuple[str, ...]     = field(default_factory=tuple)
    note:          Optional[str]       = None

    def is_resolved(self) -> bool:
        return self.status == ResolutionStatus.RESOLVED

    def to_dict(self) -> dict[str,
    Optional[str]]:
        """
        Convert to a dict suitable for database insertion.
        Note: candidates are not included in the record.
        """
        return {
            "caller_id":     str(self.caller_id),
            "callee_id":     str(self.callee_id) if self.callee_id is not None else None,
            "call_kind":     self.call_kind.value,
            "function_name": self.function_name,
            "call_line":     self.call_line,
            "status":        self.status.value,
            "library":       self.library,
            "resolved_path": self.resolved_path,
            "note":          self.note
        }

    def to_record(self) -> tuple:
        return (
            self.caller_id,
            self.callee_id,
            self.function_name,
            self.call_line,
            self.call_kind.value,
            self.library,
            self.resolved_path
        )


@dataclass
class CallResolutionResult:
    """
    Aggregated output returned by the CallGraphResolver.

    Attributes
    ----------
    resolved        Calls that were successfully resolved.
    ambiguous       Calls where multiple candidates matched.
    unresolved      Calls that could not be matched to any target.
    """
    resolved:   list[ResolvedCall] = field(default_factory=list)
    ambiguous:  list[ResolvedCall] = field(default_factory=list)
    unresolved: list[ResolvedCall] = field(default_factory=list)

    def all_calls(self) -> list[ResolvedCall]:
        return self.resolved + self.ambiguous + self.unresolved

    def resolved_calls(self) -> list[ResolvedCall]:
        return self.resolved

    def stats(self) -> dict:
        total = len(self.resolved) + len(self.ambiguous) + len(self.unresolved)
        return {
            "total":      total,
            "resolved":   len(self.resolved),
            "ambiguous":  len(self.ambiguous),
            "unresolved": len(self.unresolved),
            "resolution_rate": round(len(self.resolved) / total,
            3) if total else 0.0,
        }

    def to_record_list(self) -> list[dict[str,
    Optional[str]]]:
        """
        Convert all calls to a list of dicts suitable for database insertion.
        """
        return [call.to_record() for call in self.resolved_calls()]