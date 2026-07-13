FROM python:3.12-slim

# General-purpose modeling toolkit for the agent under test. Deliberately does
# NOT include py-ballisticcalc or the task generator, so the agent cannot call
# the exact engine and must build a statistical model from the data.
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    scikit-learn \
    statsmodels \
    scipy

WORKDIR /workspace
