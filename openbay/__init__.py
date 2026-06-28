"""OpenBay — BitTorrent-style peer-to-peer LLM inference.

Run frontier-scale models on pooled consumer GPUs.
v1 (this MVP): a whole-model swarm — each seeder serves a complete model,
a coordinator does matchmaking + a kudos ledger, clients stream tokens back.
"""

__version__ = "0.1.0"
