"""smoke_submit_audio.py — Submit an audio job as smoke_beekeeper.

Uses the /api/submit-multimedia-job endpoint (same as photo).
Prints the new SwarmJob id and confirms the file was saved on the server.

Input: Prince-of-Persia MP3 (the same clip used for the 1-level hive
       validation on 2026-04-18, confirmed present at the Downloads path).
Task: "Describe what happens in this recording."
"""
import sys
import os
import argparse
import requests

SERVER = 'http://localhost:8877'
USERNAME = 'smoke_beekeeper'
PASSWORD = 'smoke_pass_2026'
AUDIO_PATH = '/home/nir/Downloads/Ending of Prince of Persia - The Sands of Time (2010).mp3'
TASK = 'Describe what happens in this recording.'


def login(server, username, password):
    resp = requests.post(f'{server}/api/auth/login', json={
        'username': username, 'password': password
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise Exception(f"Login failed: {data}")
    return data['token']


def submit_audio(server, token, swarm_id, audio_path, task):
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    filename = os.path.basename(audio_path)

    resp = requests.post(
        f'{server}/api/submit-multimedia-job',
        headers={'Authorization': f'Bearer {token}'},
        files={'media_file': (filename, audio_bytes, 'audio/mpeg')},
        data={
            'task': task,
            'media_type': 'audio',
            'swarm_id': str(swarm_id),
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise Exception(f"Submit failed: {data}")
    return data['job_id']


def verify_upload(server, token, job_id):
    """Check that the server stored the file and set media_url."""
    resp = requests.get(
        f'{server}/api/job/{job_id}/status',
        headers={'Authorization': f'Bearer {token}'},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    media_url = data.get('media_url', '')
    media_type = data.get('media_type', '')
    print(f"  job {job_id}: media_type={media_type!r}, media_url={media_url!r}")

    # Confirm the file is downloadable via /uploads/
    if media_url:
        dl_url = f"{server}/uploads/{media_url.lstrip('/')}"
        dl = requests.head(dl_url, timeout=15)
        print(f"  HEAD {dl_url} -> HTTP {dl.status_code}")
        if dl.status_code == 200:
            print(f"  File confirmed accessible on server.")
        else:
            print(f"  WARNING: File not accessible (HTTP {dl.status_code}).")
    return media_url


def main():
    parser = argparse.ArgumentParser(description='Submit audio smoke test job')
    parser.add_argument('--swarm-id', type=int, required=True)
    parser.add_argument('--server', default=SERVER)
    parser.add_argument('--audio', default=AUDIO_PATH)
    parser.add_argument('--task', default=TASK)
    args = parser.parse_args()

    print(f"Logging in as {USERNAME}...")
    token = login(args.server, USERNAME, PASSWORD)
    print(f"Logged in. Token acquired.")

    print(f"Submitting audio job to swarm {args.swarm_id}...")
    print(f"  Source: {args.audio}")
    print(f"  Task:   {args.task}")
    job_id = submit_audio(args.server, token, args.swarm_id, args.audio, args.task)
    print(f"JOB_ID={job_id}")

    print(f"Verifying server-side storage...")
    media_url = verify_upload(args.server, token, job_id)

    print(f"\nAudio smoke job submitted successfully.")
    print(f"  SwarmJob id: {job_id}")
    print(f"  media_url:   {media_url}")
    print(f"  Expected path: audio/swarmjob_{job_id}/original.mp3")
    return job_id


if __name__ == '__main__':
    main()
