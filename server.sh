#!/bin/bash

exec uvicorn server:app --reload --host 0.0.0.0

