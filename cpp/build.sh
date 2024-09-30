#!/bin/bash

make clean && make -j24 && ./game "$@"
