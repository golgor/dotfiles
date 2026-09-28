"""Decide what a sync does on one host, without touching anything."""

from dataclasses import dataclass

from automation.omarchy_plugins.manifest import Plugin


@dataclass(frozen=True)
class Plan:
    install: list[Plugin]  # listed for this host, not installed
    present: list[Plugin]  # listed for this host, already installed: never touched again
    unmanaged: list[str]  # installed ids not listed for this host


def plan(plugins: list[Plugin], host: str, installed: set[str]) -> Plan:
    wanted = [p for p in plugins if p.for_host(host)]
    return Plan(
        install=[p for p in wanted if p.id not in installed],
        present=[p for p in wanted if p.id in installed],
        unmanaged=sorted(installed - {p.id for p in wanted}),
    )
