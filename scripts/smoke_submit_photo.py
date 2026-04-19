"""smoke_submit_photo.py — Submit a photo job as smoke_beekeeper.

Uses the /api/submit-multimedia-job endpoint (added to app.py).
Prints the new SwarmJob id.
"""
import sys
import os
import argparse
import requests

SERVER = 'http://localhost:8877'
USERNAME = 'smoke_beekeeper'
PASSWORD = 'smoke_pass_2026'
PHOTO_PATH = '/home/nir/Pictures/65291268.JPG'
TASK = 'What is shown in this photo?'


def login(server, username, password):
    resp = requests.post(f'{server}/api/auth/login', json={
        'username': username, 'password': password
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise Exception(f"Login failed: {data}")
    return data['token']


def submit_photo(server, token, swarm_id, photo_path, task):
    with open(photo_path, 'rb') as f:
        photo_bytes = f.read()
    filename = os.path.basename(photo_path)

    resp = requests.post(
        f'{server}/api/submit-multimedia-job',
        headers={'Authorization': f'Bearer {token}'},
        files={'media_file': (filename, photo_bytes, 'image/jpeg')},
        data={
            'task': task,
            'media_type': 'photo',
            'swarm_id': str(swarm_id),
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise Exception(f"Submit failed: {data}")
    return data['job_id']


def main():
    parser = argparse.ArgumentParser(description='Submit photo smoke test job')
    parser.add_argument('--swarm-id', type=int, required=True)
    parser.add_argument('--server', default=SERVER)
    parser.add_argument('--photo', default=PHOTO_PATH)
    parser.add_argument('--task', default=TASK)
    args = parser.parse_args()

    print(f"Logging in as {USERNAME}...")
    token = login(args.server, USERNAME, PASSWORD)
    print(f"Logged in. Token acquired.")

    print(f"Submitting photo job to swarm {args.swarm_id}...")
    job_id = submit_photo(args.server, token, args.swarm_id, args.photo, args.task)
    print(f"JOB_ID={job_id}")
    return job_id


if __name__ == '__main__':
    main()
