import time
import requests
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_FOLDER = "./dataset"

# Your Fabric details
FABRIC_WORKSPACE_ID =os.environ.get('FABRIC_WORKSPACE_ID')
FABRIC_PIPELINE_ID  = os.environ.get('FABRIC_PIPELINE_ID')   # get this from Fabric
TENANT_ID           =os.environ.get('TENANT_ID')
CLIENT_ID           =os.environ.get('CLIENT_ID')
CLIENT_SECRET  = os.environ.get('CLIENT_SECRET')

CHANGED_FILES = set()

def get_token(scope):
    resp = requests.post(
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope":         scope
        }
    )
    print(resp)
    return resp.json()["access_token"]

def upload_to_onelake(filepath, token):
    filename = os.path.basename(filepath)
    
    base_url = (
        f"https://onelake.dfs.fabric.microsoft.com/"
        f"29013523-0a16-4472-8853-1d70b1d63ea8/"
        f"61db38cf-f69d-4ffd-a180-0838c1d073c9/"
        f"Files/{filename}"
    )
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1 — create empty file
    create_resp = requests.put(
        base_url + "?resource=file",
        headers=headers
    )
    print(f"Create {filename}: {create_resp.status_code}")
    
    if create_resp.status_code not in (200, 201):
        print(f"Create failed: {create_resp.text}")
        return False
    
    # Step 2 — read file contents
    with open(filepath, "rb") as f:
        data = f.read()
    
    file_size = len(data)
    
    # Step 3 — append contents
    append_resp = requests.patch(
        base_url + f"?action=append&position=0",
        headers={**headers, "Content-Type": "application/octet-stream"},
        data=data
    )
    print(f"Append {filename}: {append_resp.status_code} — {append_resp.text}")
    
    if append_resp.status_code not in (200, 202):
        return False
    
    # Step 4 — flush to commit
    flush_resp = requests.patch(
        base_url + f"?action=flush&position={file_size}",
        headers=headers
    )
    print(f"Flush {filename}: {flush_resp.status_code} — {flush_resp.text}")
    
    return flush_resp.status_code in (200, 201)


def trigger_fabric_pipeline(token):
    url = (
        f"https://api.fabric.microsoft.com/v1/workspaces/"
        f"29013523-0a16-4472-8853-1d70b1d63ea8/"
        f"items/525b05cb-01f2-430e-ad69-df83910e2176/"
        f"jobs/instances?jobType=RunNotebook"
    )
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={}
    )

    if resp.status_code == 202:
        print("Notebook triggered successfully")
        
        location = resp.headers.get("Location", "")
        job_id = location.split("/")[-1]
        print(f"Job ID: {job_id}")
        
        # Poll every 30 seconds for 7 minutes (14 attempts)
        for i in range(14):
            time.sleep(30)
            status_url = (
                f"https://api.fabric.microsoft.com/v1/workspaces/"
                f"29013523-0a16-4472-8853-1d70b1d63ea8/"
                f"items/525b05cb-01f2-430e-ad69-df83910e2176/"
                f"jobs/instances/{job_id}"
            )
            status_resp = requests.get(
                status_url,
                headers={"Authorization": f"Bearer {token}"}
            )
            data = status_resp.json()
            status = data.get("status", "unknown")
            print(f"[{(i+1)*30}s] Job status: {status}")
            
            # Stop polling if job finished
            if status in ("Completed", "Failed", "Cancelled"):
                print(f"Job finished with status: {status}")
                if status == "Failed":
                    print(f"Failure reason: {data.get('failureReason', 'no details')}")
                break
    else:
        print(f"Failed: {resp.status_code} — {resp.text}")

class CSVChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".csv"):
            print(f"Change detected: {event.src_path}")
            CHANGED_FILES.add(event.src_path)

def run():
    handler = CSVChangeHandler()
    observer = Observer()
    observer.schedule(handler, path=WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"Watching {WATCH_FOLDER} for CSV changes...")

    try:
        while True:
            time.sleep(10)
            if CHANGED_FILES:
                print(f"\n{len(CHANGED_FILES)} file(s) changed — uploading to OneLake...")
                
                # OneLake needs storage scope
                onelake_token = get_token("https://storage.azure.com/.default")
                
                all_ok = all(upload_to_onelake(f, onelake_token) for f in CHANGED_FILES)
                
                if all_ok:
                    print("All files uploaded — triggering Fabric Pipeline...")
                    # Pipeline trigger needs Fabric scope
                    fabric_token = get_token("https://api.fabric.microsoft.com/.default")
                    trigger_fabric_pipeline(fabric_token)
                    CHANGED_FILES.clear()
                else:
                    print("Some uploads failed — pipeline not triggered")
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    run()