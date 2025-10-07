#!/usr/bin/env python3
"""
Start Celery worker for ClashArena
"""
import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '../backend')
sys.path.append(backend_path)

def start_worker(queue='all', concurrency=4):
    """Start Celery worker"""
    cmd = [
        'celery',
        '-A', 'app.core.celery_app:celery_app',
        'worker',
        '--loglevel=info',
        f'--concurrency={concurrency}'
    ]
    
    if queue != 'all':
        cmd.extend(['--queues', queue])
    else:
        cmd.extend(['--queues', 'auth,wallet,matches,referrals,admin'])
    
    print(f"Starting Celery worker with queue(s): {queue}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, cwd=backend_path)
    except KeyboardInterrupt:
        print("\nWorker stopped by user")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Start ClashArena Celery worker')
    parser.add_argument('--queue', default='all', help='Queue to process (default: all)')
    parser.add_argument('--concurrency', type=int, default=4, help='Number of worker processes (default: 4)')
    
    args = parser.parse_args()
    start_worker(args.queue, args.concurrency)
