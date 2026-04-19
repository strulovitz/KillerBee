"""smoke_submit_video.py — Submit a video job as smoke_beekeeper.

Uses the /api/submit-multimedia-job endpoint (same as photo/audio).
Prints the new SwarmJob id and confirms the file was saved on the server.
Also verifies that original_audio.mp3 was extracted alongside original.mp4.

Input: /home/nir/multimedia_smoke_assets/bigbuckbunny_30s.mp4
Task: "Describe what happens in this video."
"""
import sys
import os
import argparse
import requests

SERVER = 'http://localhost:8877'
USERNAME = 'smoke_beekeeper'
PASSWORD = 'smoke_pass_2026'
VIDEO_PATH = '/home/nir/multimedia_smoke_assets/bigbuckbunny_30s.mp4'
TASK = 'Describe what happens in this video.'


def login(server, username, password):
    resp = requests.post(f'{server}/api/auth/login', json={
        'username': username, 'password': password
    }, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise Exception(f"Login failed: {data}")
    return data['token']


def submit_video(server, token, swarm_id, video_path, task):
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    filename = os.path.basename(video_path)

    resp = requests.post(
        f'{server}/api/submit-multimedia-job',
        headers={'Authorization': f'Bearer {token}'},
        files={'media_file': (filename, video_bytes, 'video/mp4')},
        data={
            'task': task,
            'media_type': 'video',
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
    """Check that the server stored the video, set media_url, and extracted audio."""
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

    # Confirm the video is downloadable via /uploads/
    if media_url:
        dl_url = f"{server}/uploads/{media_url.lstrip('/')}"
        dl = requests.head(dl_url, timeout=15)
        print(f"  HEAD {dl_url} -> HTTP {dl.status_code}")
        if dl.status_code == 200:
            print(f"  Video confirmed accessible on server.")
        else:
            print(f"  WARNING: Video not accessible (HTTP {dl.status_code}).")

    # Confirm original_audio.mp3 was extracted
    if media_url:
        stem = os.path.splitext(media_url)[0]  # e.g. video/swarmjob_N/original
        audio_url = stem + '_audio.mp3'
        audio_dl_url = f"{server}/uploads/{audio_url}"
        audio_dl = requests.head(audio_dl_url, timeout=15)
        print(f"  HEAD {audio_dl_url} -> HTTP {audio_dl.status_code}")
        if audio_dl.status_code == 200:
            print(f"  original_audio.mp3 confirmed accessible on server.")
        else:
            print(f"  WARNING: original_audio.mp3 not accessible (HTTP {audio_dl.status_code}).")
            print(f"  (ffmpeg audio extraction may have failed at submit time.)")

    return media_url


def main():
    parser = argparse.ArgumentParser(description='Submit video smoke test job')
    parser.add_argument('--swarm-id', type=int, required=True)
    parser.add_argument('--server', default=SERVER)
    parser.add_argument('--video', default=VIDEO_PATH)
    parser.add_argument('--task', default=TASK)
    args = parser.parse_args()

    print(f"Logging in as {USERNAME}...")
    token = login(args.server, USERNAME, PASSWORD)
    print(f"Logged in. Token acquired.")

    print(f"Submitting video job to swarm {args.swarm_id}...")
    print(f"  Source: {args.video}")
    print(f"  Task:   {args.task}")
    job_id = submit_video(args.server, token, args.swarm_id, args.video, args.task)
    print(f"JOB_ID={job_id}")

    print(f"Verifying server-side storage...")
    media_url = verify_upload(args.server, token, job_id)

    print(f"\nVideo smoke job submitted successfully.")
    print(f"  SwarmJob id: {job_id}")
    print(f"  media_url:   {media_url}")
    print(f"  Expected video path: video/swarmjob_{job_id}/original.mp4")
    print(f"  Expected audio path: video/swarmjob_{job_id}/original_audio.mp3")
    return job_id


if __name__ == '__main__':
    main()
