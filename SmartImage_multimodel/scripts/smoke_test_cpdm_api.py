from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description='CPDM API smoke test with NRRD input')
    parser.add_argument('--nrrd', default='', help='Path to nrrd sample file')
    parser.add_argument('--sample-step', type=int, default=20, help='sampleStep for faster smoke test')
    parser.add_argument('--timeout', type=int, default=900, help='poll timeout seconds')
    parser.add_argument('--storage-mode', choices=('local', 'oss'), default='', help='Override MODEL_OUTPUT_STORAGE')
    parser.add_argument('--patient-id', type=int, default=1, help='patientId for OSS upload context')
    parser.add_argument('--study-id', type=int, default=1, help='studyId for OSS upload context')
    parser.add_argument('--auth-bearer', default='', help='Bearer token without "Bearer " prefix')
    args = parser.parse_args()

    if args.storage_mode:
        os.environ['MODEL_OUTPUT_STORAGE'] = args.storage_mode

    from api_gateway.app import create_app

    repo_root = Path(__file__).resolve().parents[2]
    sample = Path(args.nrrd) if args.nrrd else (repo_root / 'VSD.Brain.XX.O.MR_Flair.54193_1.nrrd')
    if not sample.is_file():
        print(f'[cpdm-smoke] sample nrrd not found: {sample}')
        return 2

    app = create_app()
    client = app.test_client()

    data = {
        'ct': (io.BytesIO(sample.read_bytes()), sample.name),
        'sampleStep': str(args.sample_step),
        'device': 'cpu',
    }
    if args.patient_id > 0:
        data['patientId'] = str(args.patient_id)
    if args.study_id > 0:
        data['studyId'] = str(args.study_id)

    headers = {}
    token = (args.auth_bearer or '').strip()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    print(f'[cpdm-smoke] submit: {sample}')
    submit = client.post('/api/cpdm/ct2pet', data=data, content_type='multipart/form-data', headers=headers)
    print(f'[cpdm-smoke] submit status={submit.status_code}')
    payload = submit.get_json(silent=True) or {}
    print(f'[cpdm-smoke] submit body={json.dumps(payload, ensure_ascii=False)}')
    if submit.status_code // 100 != 2:
        return 1

    job_id = payload.get('jobId')
    if not job_id:
        print('[cpdm-smoke] missing jobId')
        return 1

    start = time.time()
    while True:
        status = client.get(f'/api/cpdm/jobs/{job_id}')
        body = status.get_json(silent=True) or {}
        state = body.get('status')
        progress = body.get('progress')
        print(f'[cpdm-smoke] poll status={status.status_code} state={state} progress={progress}')

        if status.status_code == 404:
            print('[cpdm-smoke] job not found')
            return 1
        if state == 'completed':
            result = client.get(f'/api/cpdm/jobs/{job_id}/result')
            result_body = result.get_json(silent=True) or {}
            print(f'[cpdm-smoke] result status={result.status_code} body={json.dumps(result_body, ensure_ascii=False)}')
            png = client.get(f'/api/cpdm/outputs/{job_id}/pet.png')
            png_size = len(png.data or b'')
            location = png.headers.get('Location', '')
            print(f'[cpdm-smoke] png status={png.status_code} bytes={png_size} location={location}')
            png_ok = (png.status_code // 100 == 2) or png.status_code == 302
            return 0 if (result.status_code // 100 == 2 and png_ok) else 1
        if state == 'failed':
            print(f"[cpdm-smoke] failed: {json.dumps(body, ensure_ascii=False)}")
            return 1
        if time.time() - start > args.timeout:
            print('[cpdm-smoke] timeout')
            return 1
        time.sleep(3)


if __name__ == '__main__':
    raise SystemExit(main())
