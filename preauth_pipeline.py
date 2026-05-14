import os
import json
import time
import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ── CONFIG ────────────────────────────────────────────────────────────────────
CREDENTIALS_FILE = os.path.expanduser("~/Desktop/client_secret_387347941879-h102nv9u8lpg14tnpkiutfn23k9r7npv.apps.googleusercontent.com.json")
TOKEN_FILE       = os.path.expanduser("~/Desktop/token.json")
DIFY_API_KEY     = "dataset-preauth123456789"
DIFY_BASE_URL    = "http://localhost/v1"
UPLOADED_LOG     = os.path.expanduser("~/Desktop/uploaded_files.json")
SCOPES           = ["https://www.googleapis.com/auth/drive.readonly"]
DELAY_SECONDS    = 3

# ── ADD / REMOVE FOLDERS HERE ANYTIME ────────────────────────────────────────
FOLDERS = [
    {
        "name": "UHC Policies",
        "drive_folder_id": "1DRK0dB7q6F3kCMr0lXZVLSOHW22x6_wQ",
        "dataset_id": "fc5dc15d-8353-4ab2-8e72-c30e3ff26aa2"
    },
    {
        "name": "UHC Medical Necessity Guidelines",
        "drive_folder_id": "1BIN-_n-BlBY2tKw_HjPcN1BUZil138PX",
        "dataset_id": "25d2fc69-c423-442b-bee1-8e9fb6eff591"
    },
    # add more folders here in the future like this:
    # {
    #     "name": "Aetna Policies",
    #     "drive_folder_id": "your_drive_folder_id",
    #     "dataset_id": "your_dify_dataset_id"
    # },
]
# ─────────────────────────────────────────────────────────────────────────────


def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def list_drive_pdfs(service, folder_id):
    results = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
            fields="nextPageToken, files(id, name, modifiedTime)",
            pageToken=page_token
        ).execute()
        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def load_uploaded_log():
    if os.path.exists(UPLOADED_LOG):
        with open(UPLOADED_LOG, "r") as f:
            return json.load(f)
    return {}


def save_uploaded_log(log):
    with open(UPLOADED_LOG, "w") as f:
        json.dump(log, f, indent=2)


def download_pdf(service, file_id, filename):
    request = service.files().get_media(fileId=file_id)
    temp_path = f"/tmp/{filename}"
    with open(temp_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return temp_path


def upload_to_dify(filepath, filename, dataset_id):
    url = f"{DIFY_BASE_URL}/datasets/{dataset_id}/document/create-by-file"
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    data = {
        "process_rule": '{"mode": "automatic"}',
        "indexing_technique": "high_quality"
    }
    with open(filepath, "rb") as f:
        files = {"file": (filename, f, "application/pdf")}
        response = requests.post(url, headers=headers, data=data, files=files)
    return response.status_code, response.json()


def sync_folder(service, folder, uploaded_log):
    print(f"\n  📁 {folder['name']}")
    print(f"  {'─' * 45}")

    drive_files = list_drive_pdfs(service, folder["drive_folder_id"])
    new_files = [f for f in drive_files if f["id"] not in uploaded_log]

    print(f"  Found in Drive  : {len(drive_files)} PDFs")
    print(f"  Already synced  : {len(drive_files) - len(new_files)}")
    print(f"  New to upload   : {len(new_files)}")

    if not new_files:
        print(f"  ✓ Already up to date")
        return 0, []

    success = 0
    failed = []

    for i, file in enumerate(new_files, 1):
        filename = file["name"]
        file_id = file["id"]
        print(f"\n  [{i}/{len(new_files)}] {filename} ...", end=" ", flush=True)

        try:
            temp_path = download_pdf(service, file_id, filename)
            status_code, result = upload_to_dify(temp_path, filename, folder["dataset_id"])
            os.remove(temp_path)

            if status_code in (200, 201):
                print("✓")
                uploaded_log[file_id] = {
                    "name": filename,
                    "folder": folder["name"],
                    "dataset_id": folder["dataset_id"],
                    "modifiedTime": file["modifiedTime"]
                }
                save_uploaded_log(uploaded_log)
                success += 1
            else:
                print(f"✗ ({status_code}) {result.get('message', result)}")
                failed.append(filename)

        except Exception as e:
            print(f"✗ error: {e}")
            failed.append(filename)

        if i < len(new_files):
            time.sleep(DELAY_SECONDS)

    return success, failed


def main():
    print("═" * 55)
    print("  PreAuth.ai — Multi-Folder Ingestion Pipeline")
    print("═" * 55)

    print("\n[1] Authenticating with Google Drive...")
    service = get_drive_service()
    print("    ✓ Connected")

    uploaded_log = load_uploaded_log()

    total_success = 0
    total_failed = []

    print(f"\n[2] Syncing {len(FOLDERS)} folder(s)...")
    for folder in FOLDERS:
        success, failed = sync_folder(service, folder, uploaded_log)
        total_success += success
        total_failed.extend(failed)

    print(f"\n{'═' * 55}")
    print(f"  All folders synced")
    print(f"  Uploaded this run : {total_success} files")
    if total_failed:
        print(f"  Failed ({len(total_failed)}):")
        for f in total_failed:
            print(f"    - {f}")
    print(f"  Log saved → {UPLOADED_LOG}")
    print("═" * 55)
    print("\n  Tip: run this script anytime to sync new files.")
    print("  Add new folders in the FOLDERS list at the top.\n")


if __name__ == "__main__":
    main()