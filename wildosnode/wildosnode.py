#!/usr/bin/env python3
"""Startup for WildosNode"""
import asyncio

from wildosnode.wildosnode import main

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
