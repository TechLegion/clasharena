#!/usr/bin/env python3
"""
Script to run Celery workers for ClashArena
"""
import os
import sys
sys.path.append(os.path.dirname(__file__))

from app.core.celery_app import celery_app

if __name__ == '__main__':
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=4',
        '--queues=auth,wallet,matches,referrals,admin'
    ])
