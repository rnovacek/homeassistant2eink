#!/bin/bash

DEVICE="740A06B9"

exec http https://api.m5stack.com/v1/${DEVICE}/exec @main.py

