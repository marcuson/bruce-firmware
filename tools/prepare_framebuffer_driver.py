"""Prepare the private DisplayDrivers library for the framebuffer build."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

Import("env")

project = Path(env.subst("$PROJECT_DIR"))
upstream = project / "lib/DisplayDrivers"
patch = project / "patches/tftespi-framebuffer.patch"
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
storage = Path(env.subst("$BUILD_DIR")) / "local-libraries"
driver = storage / "DisplayDriversFramebuffer"
stamp = driver / ".framebuffer-version"
version = revision + ":" + hashlib.sha256(patch.read_bytes()).hexdigest()

if not stamp.exists() or stamp.read_text() != version:
    if driver.exists():
        shutil.rmtree(driver)
    archive = subprocess.check_output(["git", "archive", "--format=zip", revision, "src", "library.json"], cwd=upstream)
    with zipfile.ZipFile(io.BytesIO(archive)) as files:
        files.extractall(driver)
    # Apply paths relative to the copy, even inside the main Git checkout.
    result = subprocess.run(["git", "apply", str(patch)], cwd=driver,
                            env={**os.environ, "GIT_CEILING_DIRECTORIES": str(storage)})
    if result.returncode:
        raise RuntimeError(f"Cannot apply {patch.name} to DisplayDrivers {revision}")
    manifest = driver / "library.json"
    metadata = json.loads(manifest.read_text())
    metadata["name"] = driver.name
    manifest.write_text(json.dumps(metadata, indent=2) + "\n")
    stamp.write_text(version)

env.Prepend(LIBSOURCE_DIRS=[str(storage)])
print(f"Framebuffer driver: {driver} (upstream {revision})")
# The longer environment name can push the final linker command over the shell limit.
env.Replace(MAXLINELENGTH=8192)
