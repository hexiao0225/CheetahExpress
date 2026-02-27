"""
NOTE: This script is no longer needed.

Driver data is now fetched directly from the Yutori API in real-time.
Neo4j is only used for logging decisions (compliance checks, rankings, voice calls, assignments).

Drivers are NOT stored in Neo4j anymore - they come from Yutori API with live GPS data.
"""

print("⚠️  Driver seeding is no longer needed.")
print("Driver data is fetched from Yutori API in real-time.")
print("Neo4j is only used for decision logging, not driver storage.")
