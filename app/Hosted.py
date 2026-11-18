"""Hosted entrypoint: generate an isolated synthetic demo once per server session."""

import runpy
from pathlib import Path

import streamlit as st

from investopt.demo import demo
from investopt.paths import paths


@st.cache_resource(show_spinner="Preparing reproducible synthetic data and models…")
def prepare_hosted_demo():
    project = paths()
    if not (project.artifacts / "demo_manifest.json").exists():
        demo(seed=42, leads=1500, root=project.root)


prepare_hosted_demo()
runpy.run_path(str(Path(__file__).with_name("Home.py")), run_name="__main__")
