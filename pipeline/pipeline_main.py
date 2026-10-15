"""Legacy entrypoint forwarding to the real-data build pipeline."""
import sys
from scripts.build_all import build_all

def run_pipeline():
    print("Notice: 'pipeline.pipeline_main' has been superseded by 'scripts.build_all'.")
    print("Forwarding execution to scripts.build_all.build_all()...\n")
    build_all()

if __name__ == "__main__":
    run_pipeline()

